#!/bin/bash

set -euxo pipefail

flask db init
flask db migrate || true
flask db upgrade || true
splunk-py-trace python app.py
