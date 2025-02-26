# Use Python 3.12 slim-bullseye as the base image
FROM python:3.12-slim-bullseye

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose port 5000
EXPOSE 5000

# Install system dependencies
# hadolint ignore=DL3008
RUN apt-get update -y && \
    apt-get install -yq --no-install-recommends \
            ca-certificates \
            build-essential \
            curl \
            gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /var/cache/apt/archive/*.deb

RUN curl -LsSf https://astral.sh/uv/install.sh | env UV_UNMANAGED_INSTALL="/usr/local/bin" sh

# Install uv (a faster alternative to pip)
#RUN pip install --upgrade pip
#RUN pip install --no-cache-dir uv
RUN uv venv
ENV PATH="/.venv/bin:$PATH"

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt requirements.txt

# Install Python dependencies using uv
RUN uv pip install --system -r requirements.txt

# Copy the rest of the application code
COPY . .

# Set the entrypoint command
CMD ["/app/entrypoint.sh"]
