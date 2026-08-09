#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
search_term="${1:-ugc}"
product_url="${2:-}"

if [[ -z "$product_url" ]]; then
  printf 'Usage: ./scripts/smoke.sh SEARCH_TERM PRODUCT_URL\n' >&2
  exit 1
fi

python3 "$repo_root/scripts/viralview.py" verify-key
python3 "$repo_root/scripts/viralview.py" search-library --query "$search_term" --limit 3
python3 "$repo_root/scripts/viralview.py" scan-product --url "$product_url"

printf 'Smoke test passed. No image or video generation was submitted.\n'
