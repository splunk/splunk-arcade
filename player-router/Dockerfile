# Build stage
FROM --platform=$BUILDPLATFORM golang:1.23-bookworm AS builder

ARG TARGETOS
ARG TARGETARCH
ARG VERSION

WORKDIR /app

RUN mkdir build

COPY . .

RUN go mod download && \
    CGO_ENABLED=0 \
    GOOS=$TARGETOS \
    GOARCH=$TARGETARCH \
    go build \
    -ldflags "-s -w" \
    -trimpath \
    -a \
    -o build/player-router main.go

# Final stage
FROM --platform=$TARGETPLATFORM gcr.io/distroless/static-debian12:nonroot

WORKDIR /app
COPY --from=builder /app/build/player-router .
USER nonroot:nonroot

ENTRYPOINT ["/app/player-router"]