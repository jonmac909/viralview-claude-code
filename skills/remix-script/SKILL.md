---
name: remix-script
description: Rewrite, save, edit, and approve Viral View V6 scene dialogue while preserving source beats, target-product facts, scene timing, and speaking pace.
---

# Remix a script

Use `source_analysis` results, the saved scene map, and confirmed product-page facts. Keep the original hook, proof, scene order, and call to action unless the user asks to change them. Do not invent product claims.

1. Call `script_draft` with the source scenes, dialogue, target product facts, and requested rewrite mode.
2. Check each line against its scene duration. Use 3.2 to 4.4 spoken words per second as a warning range; keep complete, natural sentences.
3. Show the user the draft scene by scene, including warnings and any claim that needs confirmation.
4. After requested changes, save the draft with `script_draft_save`. Use `script_edit_line` for a specific line edit.
5. Call `script_approve` only after the user explicitly approves the saved script.

Script approval does not authorize character, frame, video, or export spending. Each paid batch still needs its own quote and an explicit `yes`.
