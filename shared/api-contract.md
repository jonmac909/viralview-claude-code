# Viral View public API map

Base URL: `https://app.viralview.io`

Authentication: `Authorization: Bearer $VIRALVIEW_API_KEY`

Use `python3 scripts/viralview.py`. It restricts requests to the public pipeline allowlist, rejects credentials inside JSON payloads, redacts responses, and writes secret-free request metadata to `logs/viralview-api.jsonl`.

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
