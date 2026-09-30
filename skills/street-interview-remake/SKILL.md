---
name: street-interview-remake
description: Rebuild a multi-shot, multi-person street interview ad for a new product with source analysis, grounded script rewrite, approved characters, quoted frames and Seedance videos, editor updates, and export.
---

# Remake a street interview ad

Use the V6 MCP tools. Read `../../shared/spend-policy.md` and `../../shared/api-contract.md` first.

1. Run `product_scan`, review the facts with the user, then create the V6 project with `project_create`. Return the app link.
2. Find candidates with `source_matches`. Present multi-shot, multi-person options and wait for a source choice. For a supplied video link, use `source_extract` and poll before `source_select`.
3. Run `source_analysis`. Show interview turns, hook, claims, proof, speaker changes, scene cuts, timestamps, and transcript. Wait for cut approval. Save supplied-source analysis with `source_analysis_save` when required.
4. Use `$product-swap-rewrite` with only the source breakdown and scanned product-page facts. Show the script and speaking-rate warnings. Save via `script_draft_save`, apply edits with `script_edit_line`, and wait for the user's script approval before `script_approve`.
5. Prepare a cast prompt for each needed interview role. Call `characters_quote`, show model, number of options, and estimated credits, then ask for a fresh explicit `yes`. After approval, call `characters_generate` with the exact same payload and token. Present the options and wait for the user's character choices. Save chosen identities with `character_lock` or `character_use_saved`.
6. Call `frames_quote` for all or selected scenes, including the character, scene, model, and product-photo choice. Show the estimate and wait for a new `yes`; then call `frames_generate` with the same payload and token. Review the resulting frames before making videos.
7. Call `videos_quote` with action `scene_videos`, model `seedance-2-5`, quality `480p`, and each selected scene's duration. Show model, scene count, seconds, and estimated credits. Wait for a fresh `yes`; then call `videos_generate` with the exact quoted payload and token. For a single scene regeneration, quote `scene_regenerate` again and ask for another `yes`.
8. If the user requests trim or caption-style changes, load the latest project with `project_status`, update only the editor fields present in that snapshot, and save through `editor_update`. Do not invent an editor field or claim a scene deletion was saved when the API contract does not expose it.
9. Call `export_quote`, show the estimate, and wait for a new explicit `yes`. Call `export_start` with the same payload and token, poll `export_status`, and return the final URL or `export_download` result.

Every paid batch needs its own quote and explicit user `yes`. Keep the approval token only in the quote and dispatch calls. Character or scene approval never authorizes later spend.
