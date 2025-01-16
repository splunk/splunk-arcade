FROM golang:1.23-bookworm as builder

ARG VERSION

WORKDIR /app

RUN mkdir build

COPY . .

RUN go mod download && \
    CGO_ENABLED=0 \
    GOOS=linux \
    GOARCH=amd64 \
    go build \
    -ldflags "-s -w" \
    -trimpath \
    -a \
    -o \
    build/player-router \
    main.go

FROM gcr.io/distroless/static-debian12:nonroot

WORKDIR /app
COPY --from=builder /app/build/player-router .
USER nonroot:nonroot

ENTRYPOINT ["/app/player-router"]