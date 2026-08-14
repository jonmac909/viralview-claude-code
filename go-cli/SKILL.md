---
name: pp-viralview
description: "Printing Press CLI for Viralview. Safe local CLI and MCP for the Viral View public API"
author: "Jon Mac"
license: "Apache-2.0"
argument-hint: "<command> [args] | install cli|mcp"
allowed-tools: "Read Bash"
metadata:
  openclaw:
    requires:
      bins:
        - viralview-pp-cli
---

# Viralview — Printing Press CLI

## Prerequisites: Build the local CLI

This skill drives the source-backed `viralview-pp-cli` binary in this repository. It is not published through the Printing Press library or another package installer.

```bash
cd go-cli
make build-all
./bin/viralview-pp-cli --version
```

Use the local `bin/viralview-pp-cli` and `bin/viralview-pp-mcp` paths for the agent/runtime that invokes this skill. Do not claim a package-install or release path until one is explicitly published.

## Future public release template

The following generator-owned installer block applies only after a Viral View CLI is explicitly published through the Printing Press library. It does not apply to this source checkout. Until then, use the local build steps above.

## Prerequisites: Install the CLI

This skill drives the `viralview-pp-cli` binary. **You must verify the CLI is installed before invoking any command from this skill.** If it is missing, install it first:

1. Install via the Printing Press installer. It defaults binaries to `$HOME/.local/bin` on macOS/Linux and `%LOCALAPPDATA%\Programs\PrintingPress\bin` on Windows:
   ```bash
   npx -y @mvanhorn/printing-press-library install viralview --cli-only
   ```
2. Verify: `viralview-pp-cli --version`
3. Ensure the reported install directory is on `$PATH` for the agent/runtime that will invoke this skill.

If the `npx` install fails before this CLI has a public-library category, install Node or use the category-specific Go fallback after publish.

If `--version` reports "command not found" after install, the runtime cannot see the binary directory on `$PATH`. Do not proceed with skill commands until verification succeeds.

Safe local CLI and MCP for the Viral View public API

## Command Reference

**account** — Inspect account health, balance, and usage

- `viralview-pp-cli account balance` — Read available generation-provider credits
- `viralview-pp-cli account status` — Check generation-provider reachability
- `viralview-pp-cli account usage` — List recent generation and export usage

**library** — Search approved Viral View source ads

- `viralview-pp-cli library get` — Load one approved source ad
- `viralview-pp-cli library search` — Search the approved Ad Library

**product** — Inspect a product page before creating or generating anything

- `viralview-pp-cli product` — Extract editable product facts from a public product URL

**projects** — Inspect saved Viral View projects

- `viralview-pp-cli projects get` — Load one owned project
- `viralview-pp-cli projects list` — List owned projects

**task_status** — Poll existing Viral View jobs without submitting another job

- `viralview-pp-cli task-status export-status` — Poll an existing export job
- `viralview-pp-cli task-status extraction-status` — Poll an existing source-link extraction job
- `viralview-pp-cli task-status image-status` — Poll an existing paid image job without spending again


### Finding the right command

When you know what you want to do but not which command does it, ask the CLI directly:

```bash
viralview-pp-cli which "<capability in your own words>"
```

`which` resolves a natural-language capability query to the best matching command from this CLI's curated feature index. Exit code `0` means at least one match; exit code `2` means no confident match — fall back to `--help` or use a narrower query.

## Auth Setup

Run `viralview-pp-cli auth setup` for the URL and steps to obtain a token (add `--launch` to open the URL). Then store it:

```bash
viralview-pp-cli auth set-token YOUR_TOKEN_HERE
```

Or set `VIRALVIEW_API_KEY` as an environment variable.

Run `viralview-pp-cli doctor` to verify setup.

## Agent Mode

Add `--agent` to any command. Expands to: `--json --compact --no-input --no-color --yes`.

- **Pipeable** — JSON on stdout, errors on stderr
- **Filterable** — `--select` keeps a subset of fields. Dotted paths descend into nested structures; arrays traverse element-wise. Critical for keeping context small on verbose APIs:

  ```bash
  viralview-pp-cli library get mock-value --agent --select success
  ```
- **Previewable** — `--dry-run` shows the request without sending
- **Offline-friendly** — sync/search commands can use the local SQLite store when available
- **Non-interactive** — never prompts, every input is a flag
- **Explicit retries** — use `--idempotent` only when an already-existing create should count as success

### Response envelope

Commands that read from the local store or the API wrap output in a provenance envelope:

```json
{
  "meta": {"source": "live" | "local", "synced_at": "...", "reason": "..."},
  "results": <data>
}
```

Parse `.results` for data and `.meta.source` to know whether it's live or local. A human-readable `N results (live)` summary is printed to stderr only when stdout is a terminal AND no machine-format flag (`--json`, `--csv`, `--compact`, `--quiet`, `--plain`, `--select`) is set — piped/agent consumers and explicit-format runs get pure JSON on stdout.

## Paths and state

Agents should treat the CLI's path resolver as part of the runtime contract:

- Use `--home <dir>` for one invocation, or set `VIRALVIEW_HOME=<dir>` to relocate all four path kinds under one root.
- Use per-kind env vars only when a specific kind must diverge: `VIRALVIEW_CONFIG_DIR`, `VIRALVIEW_DATA_DIR`, `VIRALVIEW_STATE_DIR`, `VIRALVIEW_CACHE_DIR`.
- Resolution order is per-kind env var, `--home`, `VIRALVIEW_HOME`, XDG (`XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_STATE_HOME`, `XDG_CACHE_HOME`), then platform defaults.
- `config` contains settings like `config.toml` and profiles. `data` contains `credentials.toml`, `data.db`, cookies, and auth sidecars. `state` contains persisted queries, jobs, and `teach.log`. `cache` contains regenerable HTTP/cache files.
- Stored secrets live in `credentials.toml` under the data dir. Existing legacy `config.toml` secrets are read for compatibility and leave `config.toml` on the first auth write.
- Run `viralview-pp-cli doctor --fail-on warn` to surface path and credential-location warnings. `agent-context` exposes a schema v4 `paths` block for agents that need the resolved dirs.
- For MCP, pass relocation through the MCP host config. The MCP binary does not inherit CLI flags:

  ```json
  {
    "mcpServers": {
      "viralview": {
        "command": "viralview-pp-mcp",
        "env": {
          "VIRALVIEW_HOME": "/srv/viralview"
        }
      }
    }
  }
  ```

Fleet precedence: an inherited per-kind env var overrides an explicit `--home` for that kind. Use `VIRALVIEW_HOME` or per-kind vars as durable fleet levers, and use `--home` only for a single invocation. Relocation is not reversible by unsetting env vars; move files manually before clearing `VIRALVIEW_HOME`, or `doctor` will not find credentials left under the former root.

## Agent Feedback

When you (or the agent) notice something off about this CLI, record it:

```
viralview-pp-cli feedback "the --since flag is inclusive but docs say exclusive"
viralview-pp-cli feedback --stdin < notes.txt
viralview-pp-cli feedback list --json --limit 10
```

Entries are stored locally as `feedback.jsonl` under the resolved data dir. They are never POSTed unless `VIRALVIEW_FEEDBACK_ENDPOINT` is set AND either `--send` is passed or `VIRALVIEW_FEEDBACK_AUTO_SEND=true`. Default behavior is local-only.

Write what *surprised* you, not a bug report. Short, specific, one line: that is the part that compounds.

## Output Delivery

Every command accepts `--deliver <sink>`. The output goes to the named sink in addition to (or instead of) stdout, so agents can route command results without hand-piping. Three sinks are supported:

| Sink | Effect |
|------|--------|
| `stdout` | Default; write to stdout only |
| `file:<path>` | Atomically write output to `<path>` (tmp + rename) |
| `webhook:<url>` | POST the output body to the URL (`application/json` or `application/x-ndjson` when `--compact`) |

Unknown schemes are refused with a structured error naming the supported set. Webhook failures return non-zero and log the URL + HTTP status on stderr.

## Named Profiles

A profile is a saved set of flag values, reused across invocations. Use it when a scheduled or recurring agent reuses the same saved flags while providing different input each run.

```
viralview-pp-cli profile save briefing --json
viralview-pp-cli --profile briefing library get mock-value
viralview-pp-cli profile list --json
viralview-pp-cli profile show briefing
viralview-pp-cli profile delete briefing --yes
```

Explicit flags always win over profile values; profile values win over defaults. `agent-context` lists all available profiles under `available_profiles` so introspecting agents discover them at runtime.

## Async Jobs

For endpoints that submit long-running work, the generator detects the submit-then-poll pattern (a `job_id`/`task_id`/`operation_id` field in the response plus a sibling status endpoint) and wires up three extra flags on the submitting command:

| Flag | Purpose |
|------|---------|
| `--wait` | Block until the job reaches a terminal status instead of returning the job ID immediately |
| `--wait-timeout` | Maximum wait duration (default 10m, 0 means no timeout) |
| `--wait-interval` | Initial poll interval (default 2s; grows with exponential backoff up to 30s) |

Use async submission without `--wait` when you want to fire-and-forget; use `--wait` when you want one command to return the finished artifact.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 2 | Usage error (wrong arguments) |
| 3 | Resource not found |
| 4 | Authentication required |
| 5 | API error (upstream issue) |
| 7 | Rate limited (wait and retry) |
| 10 | Config error |

## Argument Parsing

Parse `$ARGUMENTS`:

1. **Empty, `help`, or `--help`** → show `viralview-pp-cli --help` output
2. **Starts with `install`** → ends with `mcp` → MCP installation; otherwise → see Prerequisites above
3. **Anything else** → Direct Use (execute as CLI command with `--agent`)

## MCP Server Installation

Install the MCP binary from this CLI's published public-library entry or pre-built release, then register it:

```bash
claude mcp add viralview-pp-mcp -- viralview-pp-mcp
```

Verify: `claude mcp list`

## Direct Use

1. Check if installed: `which viralview-pp-cli`
   If not found, offer to install (see Prerequisites at the top of this skill).
2. Match the user query to the best command from the Unique Capabilities and Command Reference above.
3. Execute with the `--agent` flag:
   ```bash
   viralview-pp-cli <command> [subcommand] [args] --agent
   ```
4. If ambiguous, drill into subcommand help: `viralview-pp-cli <command> --help`.
