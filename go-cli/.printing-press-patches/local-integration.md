# Local Viral View integration patches

The generated Go module is intentionally source-backed in `viralview-claude-code` and has not been published through the Printing Press public library.

Local changes after the initial print:

- `README.md`, `SKILL.md`, and `AGENTS.md` describe local builds and stdio-only MCP use. `SKILL.md` preserves the generator-required installer template only as a clearly marked future-release block. None of these files claim a current npm installer, release artifact, MCPB bundle, Homebrew formula, or remote MCP service exists.
- `Makefile` builds both binaries with a local `VERSION` value supplied through linker flags.
- `.printing-press.json` and `manifest.json` use `VIRALVIEW_API_KEY` as a sensitive bearer-token setting. The generator's generic platform-profile metadata is not valid for Viral View's bearer-token API.
- `internal/cli/promoted_product.go` reports `meta.source: "dry-run"` when product scanning is previewed. `promoted_product_test.go` protects that no-network provenance contract.
- `cmd/viralview-pp-mcp/main.go` uses `RegisterViralViewTools`, the reviewed base account/project/library tool set plus the V6 lifecycle tools. It excludes the generator's generic SQL, import, workflow, sync, and Cobra-tree tools.
- `internal/cli/root.go` exposes only the reviewed Viral View command groups. The generator's generic local-store, import, sync, workflow, and feedback commands remain unregistered because they do not belong to this API contract.
- `internal/mcp/v6_tools.go` hand-registers the V6 project lifecycle endpoints because the Printing Press generator is unavailable locally. It keeps quote calls read-only, refuses missing approval tokens before creating an API client, forwards approval tokens only in `X-ViralView-Approval`, and redacts API credentials from results and errors. `RegisterViralViewTools` calls `RegisterV6Tools`; the V6 manifest and source spec describe the same endpoint set.
- `internal/mcp/v6_tools_test.go` uses `httptest.Server` for quote, approval-header, payload-binding, error-code, and annotation checks. It never calls the live API.

On reprint, preserve these changes or move the manifest behavior upstream before publishing anything.
