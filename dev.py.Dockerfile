FROM python:3.12-slim-bullseye

ENV PYTHONUNBUFFERED=1
EXPOSE 5000

# hadolint ignore=DL3008
RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    ca-certificates \
    build-essential \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY cabinet/requirements.txt cabinet-requirements.txt
COPY portal/requirements.txt portal-requirements.txt
COPY quiz/requirements.txt quiz-requirements.txt
COPY scoreboard/requirements.txt scoreboard-requirements.txt
RUN pip install --no-cache-dir -r cabinet-requirements.txt -r portal-requirements.txt -r quiz-requirements.txt -r scoreboard-requirements.txt

ENTRYPOINT ["sleep", "infinity"]
