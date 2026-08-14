# Viral View Go CLI

This is a locally generated Go CLI and stdio MCP server for the safe Viral View public API surface. It was generated with [CLI Printing Press](https://github.com/mvanhorn/cli-printing-press) from the checked-in [source contract](../specs/viralview-printing-press.yaml).

It is source-backed in this repository. It has not been published to the Printing Press library, npm, Homebrew, GitHub Releases, or as a remote MCP service.

## Scope

The CLI supports these non-billed workflows:

- List and load saved projects.
- Search and inspect the approved Ad Library.
- Check provider balance, status, and recent usage.
- Poll existing extraction, image, and export jobs without submitting another job.
- Scan a public product page for editable facts.

Paid image and video submission endpoints are intentionally excluded. The public API requires an explicit in-chat approval before every paid batch. Use the existing [`scripts/viralview.py`](../scripts/viralview.py) client for those operations because it enforces `--confirm-paid YES`.

## Quick Start

### Build locally

Requirements: Go 1.26.6 or newer and a Viral View developer API key when making live requests.

```bash
cd go-cli
make build-all
```

The build writes these local, ignored artifacts:

```text
bin/viralview-pp-cli
bin/viralview-pp-mcp
```

To label a local build differently:

```bash
make build-all VERSION=0.1.0
```

### Configure and use

Use an environment variable for automation. Do not put the key in a command argument, JSON payload, checked-in file, or MCP prompt.

```bash
export VIRALVIEW_API_KEY="vv_live_..."

./bin/viralview-pp-cli doctor
./bin/viralview-pp-cli projects list --json
./bin/viralview-pp-cli library search --query claymation --style animation --limit 12 --json
./bin/viralview-pp-cli account usage --limit 25 --json
./bin/viralview-pp-cli task-status image-status --task-id TASK_ID --json
```

Every command also supports `--agent` for compact JSON output and `--dry-run` to inspect the request without sending it.

```bash
./bin/viralview-pp-cli product --url https://example.com --dry-run --agent
```

`auth set-token` can store a developer key in the CLI's local credentials file with restrictive permissions. Environment variables are the preferred automation path.

## Agent Usage

Use `--agent` when an agent or script consumes the result. It enables JSON, compact fields, no input prompts, no color, and approved non-interactive defaults. Pair it with `--select` when only a few fields are needed.

```bash
./bin/viralview-pp-cli library search --query claymation --limit 12 --agent --select items,nextCursor
```

Do not use an agent command to submit paid image or video generation. That approval-gated work remains in `scripts/viralview.py`.

## Health Check

`doctor` validates the local configuration and checks the authenticated API path without printing the key.

```bash
./bin/viralview-pp-cli doctor
```

Use `auth status` to confirm that a credential is present without making a network request.

## Local MCP

The MCP server communicates over stdio only. It does not listen on a network port and must not be exposed as a public or remote service.

Build it with `make build-all`, then configure an MCP host with the absolute local binary path:

```json
{
  "mcpServers": {
    "viralview": {
      "command": "/absolute/path/to/viralview-claude-code/go-cli/bin/viralview-pp-mcp",
      "env": {
        "VIRALVIEW_API_KEY": "vv_live_..."
      }
    }
  }
}
```

The MCP tool surface matches this module's safe 11-command contract. It cannot submit paid image or video generation.

## Recipes

### Find candidate source ads

```bash
./bin/viralview-pp-cli library search --query claymation --style animation --limit 12 --json
```

### Preview a product scan without sending it

```bash
./bin/viralview-pp-cli product --url https://example.com --dry-run --agent
```

### Resume an existing image job

```bash
./bin/viralview-pp-cli task-status image-status --task-id TASK_ID --json
```

## Regeneration

The source of truth is `../specs/viralview-printing-press.yaml`. Reprint with:

```bash
cli-printing-press generate \
  --spec ../specs/viralview-printing-press.yaml \
  --spec-source official \
  --output . \
  --mcp-orchestration endpoint-mirror \
  --mcp-transport stdio \
  --mcp-endpoint-tools visible \
  --force \
  --validate
```

Reprinting may replace generated files. The local integration adjustments are recorded in `.printing-press-patches/local-integration.md` and should be reapplied or incorporated upstream before publishing.

## Troubleshooting

- `401`: the developer key is missing, invalid, revoked, or not accepted by the selected API base URL.
- `402`: the account does not have active paid access.
- `403`: the request is outside the public API boundary.
- `429`: wait for the server's retry window and poll existing jobs rather than starting another request.
- Interrupted job polling: resume with the existing task or job ID. Do not submit a replacement job.

## Verification

```bash
go test ./...
go vet ./...
make build-all
./bin/viralview-pp-cli --help
```

No live test is required to verify the build. Do not send a paid request merely to validate the CLI.
