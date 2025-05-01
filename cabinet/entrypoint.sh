#!/bin/bash

set -euxo pipefail

current_datetime=$(date +"%Y-%m-%d %H:%M:%S.%3N")
echo "Start time: $current_datetime"

#splunk-py-trace python app.py
opentelemetry-instrument python app.py
