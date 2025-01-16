FROM golang:1.23-bookworm

# hadolint ignore=DL3008
RUN apt-get update -y && \
    apt-get install -yq --no-install-recommends \
            ca-certificates \
            wget \
            jq \
            procps \
            curl \
            vim \
            inetutils-ping binutils && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /var/cache/apt/archive/*.deb

WORKDIR /app

ENTRYPOINT ["sleep", "infinity"]
