# Viral View agent workspace

This repository runs Viral View workflows from Codex and other agents that support the Agent Skills format.

## Start here

1. Read `MASTER_CONTEXT.md` if it exists.
2. Run `./scripts/setup.sh` if `.env` is missing.
3. Read the relevant `skills/<name>/SKILL.md` before acting.
4. Use `python3 scripts/viralview.py` for API calls. Do not create alternate clients.

## Skill index

- `clone-viral-ad`: Run the complete product-to-video flow.
- `search-library`: Find source ads and present candidates.
- `product-scan`: Extract editable product details.
- `character-options`: Prepare, generate, and choose character options.
- `remix-script`: Adapt dialogue and check speaking pace.
- `usage-costs`: Review usage and estimate the next batch.
- `export-video`: Start or retrieve a final MP4 export.
- `street-interview-remake`: Remake a multi-shot, multi-person interview ad through V6.
- `product-swap-rewrite`: Preserve an ad's beats while grounding claims in scanned product facts.

## Hard rules

- Before every paid image or video generation batch, show the estimated credits and get an explicit user `yes` in chat. A previous approval never carries forward.
- Apply the same fresh quote and explicit `yes` requirement to other paid provider-credit actions, including product cutout and export.
- Stop for the user's choice after presenting character options and detected scene cuts.
- Never send a generation request with an estimate missing or an approval inferred from context.
- Never ask for or store an upstream provider key. The only supported credential is `VIRALVIEW_API_KEY` in the local `.env` file.
- Never print, log, summarize, or commit API keys, bearer headers, session cookies, private media, or account data.
- Never send bearer authentication to auth, billing, admin, support, internal, or API-key management routes.
- Do not trigger paid generation during setup, smoke testing, or troubleshooting.
- Keep user media under `references/`, generated logs under `logs/`, and workflow state under `.viralview/`. These paths are ignored by Git.

## Validation

Run `python3 scripts/validate.py` before committing changes to this workspace.
