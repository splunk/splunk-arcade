#!/bin/bash

if [ "$SPLUNK_ARCADE_OBSERVABILITY_API_ACCESS_TOKEN" = "REPLACE_ME" ]; then
  echo "o11y observability token not set..."
  echo "continue...? (y/n)"
  read -r choice

  if [[ "$choice" != "y" ]]; then
    exit 1
  fi
fi
