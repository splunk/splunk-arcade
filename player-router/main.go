package main

import (
	"context"
	"crypto/tls"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"sync"
	"syscall"
	"time"
)

const (
	timeoutSeconds = 5
	maxRetries     = 5
	retryDelay     = 1
)

const (
	sigsChanLen = 2
	exitCode    = 1
)

var onlyOneSignalHandler = make(chan struct{}) //nolint: gochecknoglobals

func SignalHandledContext(
	logf func(f string, a ...interface{}),
) (context.Context, context.CancelFunc) {
	defer func() {
		if r := recover(); r != nil {
			_, _ = os.Stdout.WriteString(
				"panic: requesting signal handled context, but signal handled context" +
					" already exists, there can only be one",
			)

			os.Exit(1)
		}
	}()

	// panics when called twice, this way there can only be one signal handled context
	close(onlyOneSignalHandler)

	ctx, cancel := context.WithCancel(context.Background())

	sigs := make(chan os.Signal, sigsChanLen)

	signal.Notify(sigs, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		sig := <-sigs
		logf("received signal '%s', canceling context", sig)

		cancel()

		<-sigs
		logf("received signal '%s', exiting program", sig)

		os.Exit(exitCode)
	}()

	return ctx, cancel
}

func NewServer(ctx context.Context, host string, port uint16, mux *http.ServeMux) *http.Server {
	server := &http.Server{
		BaseContext: func(_ net.Listener) context.Context {
			return ctx
		},
		Addr: fmt.Sprintf(
			"%s:%d",
			host,
			port,
		),
		Handler:           mux,
		ReadTimeout:       timeoutSeconds * time.Second,
		WriteTimeout:      timeoutSeconds * time.Second,
		ReadHeaderTimeout: timeoutSeconds * time.Second,
		TLSConfig: &tls.Config{
			MinVersion:       tls.VersionTLS12,
			CurvePreferences: []tls.CurveID{tls.CurveP521, tls.CurveP384, tls.CurveP256},
			CipherSuites: []uint16{
				tls.TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,
				tls.TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256,
				tls.TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,
				tls.TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384,
				tls.TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,
				tls.TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256,
				tls.TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256,
				tls.TLS_AES_128_GCM_SHA256,
				tls.TLS_AES_256_GCM_SHA384,
				tls.TLS_CHACHA20_POLY1305_SHA256,
			},
		},
	}

	server.SetKeepAlivesEnabled(false)

	return server
}

type Router struct {
	serverHost string
	serverPort uint16
	server     *http.Server

	shuttingDownLock *sync.RWMutex
	shuttingDown     bool
}

func (r *Router) setShuttingDown(b bool) {
	r.shuttingDownLock.Lock()
	defer r.shuttingDownLock.Unlock()

	r.shuttingDown = b
}

func (r *Router) getShuttingDown() bool {
	r.shuttingDownLock.RLock()
	defer r.shuttingDownLock.RUnlock()

	return r.shuttingDown
}

func (r *Router) health(wr http.ResponseWriter, req *http.Request) {
	log.Printf("received %q on %q endpoint from %q", req.Method, req.RequestURI, req.RemoteAddr)

	// if we're running, we're ready... hopefully :p
	wr.WriteHeader(http.StatusOK)
}

func doRequestWithRetry(client *http.Client, req *http.Request) (*http.Response, error) {
	var resp *http.Response
	var err error

	for i := 0; i < maxRetries; i++ {
		resp, err = client.Do(req)
		if err == nil {
			return resp, nil
		}

		log.Printf("attempt %d failed: %s, retrying in %ds...", i+1, err, retryDelay)

		time.Sleep(retryDelay)
	}

	return nil, fmt.Errorf("all retries failed: %w", err)
}

func (r *Router) proxy(wr http.ResponseWriter, req *http.Request) {
	log.Printf("received %q on %q endpoint from %q", req.Method, req.RequestURI, req.RemoteAddr)

	requestURIParts := strings.Split(req.RequestURI, "/")
	if len(requestURIParts) < 3 {
		http.Error(wr, "failed parsing player id from uri", http.StatusInternalServerError)

		return
	}

	playerID := requestURIParts[2]
	proxiedRequestTarget := fmt.Sprintf("http://splunk-arcade-cabinet-player-%s", playerID)

	if len(requestURIParts) > 2 {
		remainingURIPart := strings.Join(requestURIParts[2:], "/")
		proxiedRequestTarget = fmt.Sprintf("%s/player/%s", proxiedRequestTarget, remainingURIPart)
	}

	log.Printf("proxying for player %q to %q", playerID, proxiedRequestTarget)

	proxiedRequest, err := http.NewRequest(req.Method, proxiedRequestTarget, req.Body)
	if err != nil {
		log.Printf("create proxied request err: %s", err)

		http.Error(wr, "failed to create request", http.StatusInternalServerError)

		return
	}

	proxiedRequest.Header = req.Header

	client := &http.Client{
		CheckRedirect: func(req *http.Request, via []*http.Request) error {
			if req.URL.Host == "splunk-arcade.home" {
				// dont go to the public address, just pass it to the service here in the cluster
				// otherwise.... good luck?
				req.URL.Host = "splunk-arcade-portal"
			}

			return nil
		},
	}

	resp, err := doRequestWithRetry(client, proxiedRequest)
	if err != nil {
		log.Printf("do proxied request err: %s", err)

		http.Error(wr, "failed to reach service", http.StatusInternalServerError)

		return
	}

	defer resp.Body.Close()

	for key, values := range resp.Header {
		for _, value := range values {
			wr.Header().Add(key, value)
		}
	}

	wr.WriteHeader(resp.StatusCode)

	_, err = io.Copy(wr, resp.Body)
	if err != nil {
		log.Printf("write proxied response err: %s", err)

		http.Error(wr, "failed to write response back to originating client", http.StatusInternalServerError)
	}
}

func (r *Router) serve(ctx context.Context, cancel context.CancelFunc) {
	mux := http.NewServeMux()

	mux.HandleFunc(
		"/alive",
		r.health,
	)

	mux.HandleFunc(
		"/",
		r.proxy,
	)

	r.server = NewServer(ctx, r.serverHost, r.serverPort, mux)

	go func() {
		err := r.server.ListenAndServe()
		if err != nil && !r.getShuttingDown() {
			log.Printf("http server has failed, error: %s", err)

			// don't fatal out, cancel so things can try to be nicely cleaned up
			cancel()
		}
	}()
}

func main() {
	ctx, cancel := SignalHandledContext(log.Printf)

	rtr := Router{
		serverHost:       "0.0.0.0",
		serverPort:       5000,
		shuttingDownLock: &sync.RWMutex{},
	}

	log.Printf("starting to serve...")

	rtr.serve(ctx, cancel)

	select {
	case <-ctx.Done():
		log.Printf("context is done, exiting...")

		os.Exit(1)
	}
}
