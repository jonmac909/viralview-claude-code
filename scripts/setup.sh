#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
env_file="$repo_root/.env"
context_file="$repo_root/MASTER_CONTEXT.md"

command -v python3 >/dev/null 2>&1 || {
  printf 'Python 3 is required.\n' >&2
  exit 1
}

printf 'Paste your Viral View API key. Input is hidden: '
IFS= read -r -s viralview_key
printf '\n'

if [[ ! "$viralview_key" =~ ^vv_live_[0-9a-f]{32}$ ]]; then
  unset viralview_key
  printf 'That key does not match the Viral View key format.\n' >&2
  exit 1
fi

printf 'Base URL [%s]: ' 'https://app.viralview.io'
IFS= read -r viralview_base_url
viralview_base_url="${viralview_base_url:-https://app.viralview.io}"
if [[ ! "$viralview_base_url" =~ ^https:// ]] && [[ ! "$viralview_base_url" =~ ^http://(127\.0\.0\.1|localhost)(:[0-9]+)?$ ]]; then
  unset viralview_key
  printf 'Use an HTTPS URL, or localhost for development.\n' >&2
  exit 1
fi

umask 077
{
  printf 'VIRALVIEW_API_KEY=%s\n' "$viralview_key"
  printf 'VIRALVIEW_BASE_URL=%s\n' "${viralview_base_url%/}"
} > "$env_file"
chmod 600 "$env_file"
unset viralview_key

if ! python3 "$repo_root/scripts/viralview.py" verify-key >/dev/null; then
  printf 'The key was saved locally, but bearer authentication failed.\n' >&2
  printf 'Check that the Viral View public API is deployed, then rerun setup.\n' >&2
  exit 1
fi

cat > "$context_file" <<'CONTEXT'
# Viral View workspace context

Add product details, preferred ad styles, recurring character notes, and output requirements here.

Never paste API keys, authorization headers, session cookies, or provider credentials into this file.
CONTEXT
chmod 600 "$context_file"

printf 'Viral View authentication verified.\n'
printf 'Local context created at MASTER_CONTEXT.md.\n'
printf 'Open this folder in Codex or Claude Code and invoke $clone-viral-ad.\n'
