#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

printf 'Viral View agent workspace\n'
printf 'Skills: clone-viral-ad, search-library, product-scan, export-video, character-options, remix-script, usage-costs\n'
if [[ -f "$repo_root/.env" ]]; then
  printf 'API key: configured locally\n'
else
  printf 'API key: missing, run ./scripts/setup.sh\n'
fi
if [[ -f "$repo_root/MASTER_CONTEXT.md" ]]; then
  printf 'Workspace context: available\n'
else
  printf 'Workspace context: not created\n'
fi
printf 'Paid image and video batches require an explicit user yes before submission.\n'
