---
name: clone-viral-ad
description: Orchestrate the complete Viral View product-to-video pipeline from a product URL and source ad through product review, source selection, scene analysis, script remixing, character choice, frame and video generation, and final export. Use when the user asks to clone, remake, adapt, or recreate a viral ad for a product with Viral View.
---

# Clone a viral ad

Run the full workflow. Keep one active state file under `.viralview/` and show the user every human decision before advancing.

Read `../../shared/spend-policy.md` and `../../shared/api-contract.md` first.

## Workflow

1. Run `python3 skills/clone-viral-ad/scripts/clone_viral_ad.py start --product-url URL --search-term QUERY`.
2. Show the scanned name, description, product type, benefits, and images. Let the user edit them.
3. Show the best library candidates with title, duration, style, thumbnail URL, and source ID. Wait for the user's selection.
4. Load the selected library item. Create a project and save the product plus source identifiers.
5. Analyze the source with `/api/ugc/analyze-video` in `full-clone` mode. For a source link, start `/api/ugc/extract-video` and poll before analysis.
6. Present the detected scene cuts with timestamps and purposes. Wait for approval or edits. Submit approved cuts in `refine-scenes` mode.
7. Invoke `$remix-script`. Show dialogue per scene and any speaking-rate warnings. Wait for script approval.
8. Invoke `$character-options`. Before the three-image batch, show the credit estimate and get a fresh explicit `yes`. Present all returned images and wait for one choice.
9. Save the selected character and lock. Prepare identity references for the remake frames.
10. Show the frame-generation batch count and credit estimate. Get a fresh explicit `yes`, then submit the frame batch and poll every task.
11. Show the video-generation scene count, model, per-scene estimate, and total estimate. Get a fresh explicit `yes`, then submit the video batch and poll every task.
12. Invoke `$export-video`. Poll the export job and end with the final MP4 URL.

## Required stops

Stop and wait after product review, source selection, scene-cut review, script review, character selection, every image estimate, and every video estimate.

The exact word `yes` must come from the user after the current batch estimate. Never reuse an earlier approval. Never submit a paid retry automatically.

## Failure handling

- On `401`, stop and rerun setup with a new key.
- On `402`, stop and report that paid Viral View access is inactive.
- On `429`, honor `Retry-After` and do not submit a duplicate generation request.
- If a poll is interrupted, resume the existing job ID. Do not create a replacement task.
- If any item in a paid batch fails, show the failed item and its estimated retry cost. Ask for a new `yes` before retrying it.

Use `scripts/clone_viral_ad.py` to initialize and inspect workflow state. Use the sibling skill scripts for each operation.
