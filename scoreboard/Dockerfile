FROM python:3.12-slim-bullseye

ENV PYTHONUNBUFFERED=1
EXPOSE 5000

# hadolint ignore=DL3008
RUN apt-get update -y && \
    apt-get install -yq --no-install-recommends \
            ca-certificates \
            build-essential \
            gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /var/cache/apt/archive/*.deb

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && \
    splunk-py-trace-bootstrap

COPY . .

CMD ["/app/entrypoint.sh"]
