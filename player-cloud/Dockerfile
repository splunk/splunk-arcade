FROM debian:bookworm-slim

ARG TERRAFORM_VERSION=1.10.5

RUN apt-get update && \
    apt-get install -yq --no-install-recommends \
            ca-certificates \
            curl \
            unzip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /var/cache/apt/archive/*.deb

# Determine architecture and download appropriate Terraform binary
RUN ARCH=$(dpkg --print-architecture) && \
    case "$ARCH" in \
      amd64) TF_ARCH="amd64" ;; \
      arm64) TF_ARCH="arm64" ;; \
      *) echo "Unsupported architecture: $ARCH" && exit 1 ;; \
    esac && \
    curl -fsSL "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_${TF_ARCH}.zip" -o terraform.zip && \
    unzip terraform.zip && \
    chmod +x terraform && \
    mv terraform /usr/local/bin/terraform && \
    rm terraform.zip

# Copy necessary Terraform and script files
COPY entrypoint.apply.sh entrypoint.apply.sh
COPY entrypoint.destroy.sh entrypoint.destroy.sh
COPY main.tf main.tf
COPY vars.tf vars.tf

CMD ["/entrypoint.apply.sh"]