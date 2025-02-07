#!/bin/bash

set -euxo pipefail

echo "secret_suffix = \"${TF_VAR_player_name}\"" > backend.hcl

/terraform init -input=false -backend-config=backend.hcl
/terraform destroy -auto-approve