---
name: clone-viral-ad
description: Orchestrate the complete Viral View V6 product-to-video flow with project review, source selection, scene analysis, script approval, characters, frames, videos, and quote-gated export. Use when the user asks to clone or remake an ad.
---

# Clone a viral ad

Read `../../shared/spend-policy.md` and `../../shared/api-contract.md` first. Use the Viral View MCP V6 tools for project work. The only supported credential is `VIRALVIEW_API_KEY`; never ask for a provider key.

## Workflow

1. Call `product_scan` for the public product URL. Show the scanned name, description, type, benefits, and images. Let the user correct product facts.
2. Call `project_create` with the app project snapshot and confirmed product facts. Return the project ID and `https://app.viralview.io/ugc-v6?project=<id>` link.
3. Call `source_matches` with the product facts and scan context. Present the highest-ranked library sources with their titles, duration, fit reasons, and IDs. Wait for the user's choice.
4. Call `source_select` with `type: "select_source"` and the chosen library ID. For a supplied link, call `source_extract`, poll the extraction job, then use `source_select` with `type: "set_supplied_source"` and the saved upload path.
5. Call `source_analysis` and present the hook, claims, proof, transcript, scene purposes, and timestamps. Wait for the user's scene-cut choice. Save supplied-source timing with `source_analysis_save` when required.
6. Call `script_draft` with the source breakdown and only confirmed product facts. Show dialogue by scene, speaking-rate warnings, and any unsupported claim. Save with `script_draft_save`; apply requested line changes with `script_edit_line`; call `script_approve` only after the user approves the script.
7. Prepare the character prompt and call `characters_quote`. Show the model, image count, duration if present, estimated credits, and expiry. Ask for a fresh explicit `yes` in chat. After the user says yes, call `characters_generate` with the exact same payload and returned `approvalToken`. Present the options and wait for the user's selection before `character_lock` or `character_use_saved`.
8. Call `frames_quote` for all or selected scenes, with the requested model and product-photo choice. Show the estimate and ask for a new explicit `yes`. Then call `frames_generate` with the exact quoted payload and token. Let the user choose or review the finished frames before moving on.
9. Call `videos_quote` with `scene_videos` for a batch or `scene_regenerate` for one replacement. Include each scene, model, duration, and quality. Show model, item count, seconds, and estimated credits; wait for a new explicit `yes`; then call `videos_generate` with the exact same payload and token.
10. Call `export_quote`, show the export estimate, and wait for an explicit `yes`. Call `export_start` with the same payload and token, poll `export_status`, and use `export_download` for the returned same-origin upload path.

## Paid batch rule

Every character, frame, video, regeneration, automatic paid step, and export batch gets its own quote and a new explicit user `yes`. Do not call a paid tool without the current quote's token. Never reuse approval after a changed payload, failed or cancelled call, retry, or new batch. Do not store or log approval tokens.

## Failure handling

- For `approval_required` or `approval_invalid`, quote the exact payload again and ask the user before dispatch.
- For `approval_expired`, `approval_replayed`, or `over_daily_cap`, do not retry automatically. Explain the returned code and wait for the user's direction.
- On `401`, stop and have the user repair the developer key. On `429`, honor `Retry-After` and avoid duplicate submissions.
- If a poll is interrupted, resume the returned job ID. Do not create a replacement task.
