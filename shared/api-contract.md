# Viral View public API map

Base URL: `https://app.viralview.io`

Authentication: `Authorization: Bearer $VIRALVIEW_API_KEY`

Use `python3 scripts/viralview.py` for direct API calls. It restricts requests to the public pipeline allowlist, rejects credentials inside JSON payloads, redacts responses, and writes secret-free request metadata to `logs/viralview-api.jsonl`. The local Go MCP exposes the V6 workflow described below.

## Core routes

| Method | Path | Purpose |
| --- | --- | --- |
| GET, POST, DELETE | `/api/ugc/project` | List, load, save, or delete projects |
| POST | `/api/ugc/scan-product` | Extract editable product details from `productUrl` |
| GET | `/api/ugc/ad-library` | Search by `query`, `style`, `limit`, and `cursor` |
| GET | `/api/ugc/ad-library/{id}` | Load the selected source video |
| POST, GET, DELETE | `/api/ugc/extract-video` | Start, poll, or cancel a link extraction job |
| POST | `/api/ugc/analyze-video` | Analyze a source or refine approved scene cuts |
| POST | `/api/ugc/rewrite-script` | Rewrite or fit scene dialogue |
| POST | `/api/ugc/describe-character-frame` | Build an editable character prompt |
| POST | `/api/ugc/lock-character` | Build a reusable character lock |
| POST, GET | `/api/ugc/generate-overlay` | Start and poll image generation |
| POST | `/api/ugc/generate-kling` | Start or poll video generation |
| POST, GET | `/api/ugc/stitch-videos` | Start and poll the final export |
| GET | `/api/ugc/usage` | Read recent generation events and cost basis |
| GET | `/api/ugc/kie-balance` | Read the account's available generation balance |
| GET | `/api/ugc/kie-status` | Check generation service health |

## Common job lifecycle

Start calls return a `jobId` or `taskId`. Poll the same route at the documented interval. Stop on `done`, `success`, `completed`, `failed`, `error`, or `cancelled`. Do not submit a second generation request while a task is still active.

Suggested limits:

- Link extraction: poll every 5 seconds for up to 10 minutes.
- Image tasks: poll every 5 seconds for up to 30 minutes.
- Video tasks: poll every 8 seconds for up to 30 minutes.
- Export jobs: poll every 3 seconds for up to 30 minutes.

## Error handling

Errors use an HTTP status with a JSON body containing `success: false` and an `error` or `code` field. Treat `401` as an invalid or revoked key, `402` as inactive paid access, `403` as a forbidden caller or origin, `429` as rate limiting, and `5xx` as a retryable service problem unless the response says otherwise.

Never include the bearer token or an upstream provider key in request JSON, logs, issue reports, screenshots, or error messages.

## V6 project routes

The V6 MCP also calls these app routes using the same developer bearer key. Access to most V3 and upload routes is part of the app's in-progress developer-key rollout; check the deployed contract before relying on a route being open.

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/v3/project/{id}/quote` | Quote a paid action using `{action, payload}`; returns estimate, expiry, and one-time approval token |
| POST | `/api/v3/project/{id}/intent` | Persist V6 intents such as source selection, script draft/edit/approval, saved-character reuse, and export lifecycle state |
| GET | `/api/v3/project/{id}/context` | Read computed project workflow context and next actions |
| GET, POST | `/api/v3/project/{id}/frames` | Read frame state; prepare or dispatch frames (`action: prepare|dispatch`) |
| POST | `/api/v3/project/{id}/character-dispatch` | Generate character candidates |
| GET, POST | `/api/v3/project/{id}/generate` | Generate or poll scene videos |
| POST | `/api/v3/project/{id}/product-cutout` | Start or poll product-image background removal |
| POST | `/api/v3/project/{id}/auto/start` | Start the next automatic workflow action |
| POST | `/api/v3/project/{id}/auto/stop` | Stop an active automatic workflow |
| GET | `/api/v3/project/{id}/export-status` | Read the saved export job state |
| GET, POST | `/api/v3/characters` | List or save reusable characters |
| POST | `/api/ugc/source-matches` | Rank source ads for a product and scan context |
| POST | `/api/ugc/analyze-video` | Analyze hook, claims, proof, scenes, timing, and transcript |
| POST | `/api/ugc/rewrite-script` | Draft or rewrite dialogue from source and product context |
| GET | `/api/ugc/meta-ad-library/search` | Search the public Meta Ad Library integration |
| POST | `/api/upload` or `/api/upload/multipart` | Upload project media (the current MCP does not stream local files) |
| GET, HEAD | `/api/uploads/{key}` | Read/download media owned by the caller |

V3 intent names and bodies are defined by the app's `lib/v3-project-intents.ts`. Common intents include `select_source`, `set_supplied_source`, `save_supplied_source_enrichment`, `save_script_draft`, `edit_script`, `approve`, and `reuse_saved_character`. Send those app-defined intent bodies unchanged to `/intent`.

### Paid quote and dispatch

For actions supported by the app's `lib/developer-approval-payload.ts`, quote with `POST /api/v3/project/{id}/quote` and body `{action, payload}`. The quote is read-only and returns `creditsTotal`, `approvalToken`, and `expiresAt` (plus per-item details). The paired dispatch must send the exact same payload and set `X-ViralView-Approval: <approvalToken>`. Tokens are short-lived, single-use, and bound to the caller, project, action, and canonical payload. Treat HTTP `402` codes `approval_required`, `approval_invalid`, `approval_expired`, `approval_replayed`, and `over_daily_cap` as a refusal; refresh the quote and ask the user again where applicable.

Supported quote actions include `characters`, `frames`, `frame_remake`, `scene_videos`, `scene_regenerate`, `lip_redo`, `auto`, `overlay`, `export`, `product_cutout`, and `intent_retry`. The app's canonical payload builder defines model normalization, item identity, frame scene ordering, and video duration/quality. Do not build an alternate estimate locally.

The V6 MCP uses a generic `/api/ugc/project` save for the app's editor snapshot. There are no dedicated typed API routes for trimming clips, deleting a scene, or setting caption style in the inspected app routes. Local file upload is also not implemented in the MCP; select an existing uploaded media URL instead.
