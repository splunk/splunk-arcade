FROM debian:bookworm-slim

ARG TERRAFORM_VERSION=1.10.5

RUN apt-get update && \
    apt-get install -yq --no-install-recommends \
            ca-certificates \
            curl \
            unzip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /var/cache/apt/archive/*.deb

RUN ARCH=$(uname -m) && \
    curl -fsSL "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip" -o terraform.zip && \
    unzip terraform.zip && \
    chmod +x terraform && \
    rm terraform.zip

COPY entrypoint.apply.sh entrypoint.apply.sh
COPY entrypoint.destroy.sh entrypoint.destroy.sh

COPY main.tf main.tf
COPY vars.tf vars.tf

CMD ["/entrypoint.apply.sh"]
