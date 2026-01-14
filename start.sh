#!/bin/bash
set -euo pipefail

cd /home/ubuntu/money/bnb
/usr/local/bin/sops -d /home/ubuntu/money/secrets.yaml | ./.venv/bin/python3 final.py