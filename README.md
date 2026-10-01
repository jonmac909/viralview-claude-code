# Viral View for Codex and Claude Code

Clone viral video ads for your product from Codex or Claude Code using the [Viral View](https://app.viralview.io) public API.

This repository includes seven agent skills, a dependency-free Python API client, secure local setup, spend controls, job polling, smoke tests, and editor entrypoints for Codex, Claude Code, and Cursor.

## What it does

- Searches the Viral View ad library and lets you pick a source.
- Scans a product URL and returns editable product details.
- Detects scene cuts and waits for your approval.
- Rewrites dialogue with speaking-rate warnings.
- Generates three character choices and waits for your pick.
- Generates remake frames and scene videos.
- Exports the finished MP4 and returns its download URL.

## Requirements

- A paid Viral View account
- A Viral View developer API key
- Python 3.10 or newer
- Bash for setup and smoke scripts

No pip packages, Node packages, or upstream provider keys are required.

## Get started

### 1. Clone the repository

```bash
git clone https://github.com/jonmac909/viralview-claude-code.git
cd viralview-claude-code
```

### 2. Run setup

```bash
./scripts/setup.sh
```

Setup hides your input, writes the key only to a local `.env` file with restricted permissions, verifies bearer authentication, and creates a private `MASTER_CONTEXT.md` file. Both files are ignored by Git.

### 3. Open the folder

Open the repository in Codex or Claude Code. The same canonical skills are exposed through `.agents/skills/` and `.claude/skills/`. Cursor entrypoints live under `.cursor/skills/`.

### 4. Start a clone

In Codex or Claude Code:

> Use $clone-viral-ad to clone a claymation library ad for https://shadowmap.ai

The agent scans the product, presents source candidates, asks you to approve scene cuts and dialogue, shows credit estimates before paid work, presents three character images, generates the approved frames and videos, then returns the final MP4 URL.

## Mandatory spend control

Every paid image or video batch requires its own confirmation. Product cutouts use the same fresh quote and confirmation rule. Final exports are render jobs and do not spend provider credits:

1. The agent shows the model, item count, per-item estimate, and total estimated credits.
2. You reply `yes` in the current chat.
3. The client submits only that exact batch.

A retry, regeneration, model change, changed batch size, frame stage, and video stage each need a new estimate and a new `yes`. The client blocks direct image or video requests without the confirmation flag. Start an export with `export_start`, then poll `export_status`.

## Skills

| Skill | Purpose |
| --- | --- |
| `$clone-viral-ad` | Run the complete product-to-MP4 workflow |
| `$search-library` | Find and compare source ads |
| `$product-scan` | Extract editable product facts and images |
| `$character-options` | Prepare, generate, and choose a character |
| `$remix-script` | Rewrite dialogue and check timing |
| `$usage-costs` | Review usage and estimate the next batch |
| `$export-video` | Retrieve or create the final export |

## Useful commands

```bash
# Verify all skill, script, copy, and secret checks
python3 scripts/validate.py

# Confirm authentication without printing the key
python3 scripts/viralview.py verify-key

# Run no-generation smoke checks
./scripts/smoke.sh "claymation" "https://shadowmap.ai"

# Inspect recent usage and balance
python3 skills/usage-costs/scripts/usage_costs.py recent
```

The smoke script runs authentication, library search, and product scanning only. It does not submit image or video generation.

## Go CLI and local MCP

`go-cli/` is a generated Go CLI and stdio MCP server for the Viral View API. It includes the V6 project workflow with quote-gated paid steps. It is source-backed in this repository and has not been published as an npm package, Homebrew formula, release artifact, or remote MCP service.

```bash
cd go-cli
make build-all
export VIRALVIEW_API_KEY="vv_live_..."
./bin/viralview-pp-cli library search --query claymation --limit 12 --json
```

Paid MCP tools require a fresh quote and its one-time approval token; the tool descriptions and annotations ask the host to obtain user approval before dispatch. The Python client keeps `--confirm-paid YES` as an additional local guard. See [the Go CLI guide](go-cli/README.md) and [its source contract](specs/viralview-printing-press.yaml).

## Security

- The only supported credential is `VIRALVIEW_API_KEY` in `.env`.
- `.env`, personal context, logs, workflow state, and reference media are ignored.
- The client rejects API keys, tokens, bearer headers, passwords, and secrets inside request JSON.
- The client only sends bearer authentication to the public Viral View pipeline allowlist.
- Request logs contain method, path, status, and duration only.
- Responses are redacted before printing.
- `scripts/check_secrets.py` scans public files and full Git history for likely credentials.

Never paste a key into chat, a prompt, `MASTER_CONTEXT.md`, an issue, or a pull request. Revoke a key immediately if it is exposed.

See [SECURITY.md](SECURITY.md) for private vulnerability reporting.

## Troubleshooting

- `401`: The key is invalid, revoked, or bearer authentication is not active on the selected base URL.
- `402`: The Viral View account does not have active paid access.
- `403`: The route or caller is outside the public pipeline boundary.
- `429`: Wait for the server's retry window. Do not submit a duplicate generation task.
- Interrupted polling: Resume the existing job ID instead of starting a new paid request.

Run `python3 scripts/viralview.py --help` for the low-level client commands.

## License

[MIT](LICENSE)
