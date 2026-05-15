#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ -d .git ]]; then
  echo "Fixture git repo already initialized."
  exit 0
fi
git init -b main
git add sample_module.py README.md
git commit -m "chore: phase1 fixture initial commit"
echo "Fixture git repo initialized on branch main."
