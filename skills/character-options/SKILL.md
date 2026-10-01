---
name: character-options
description: Prepare and generate Viral View character options through the V6 MCP with a fresh quote and explicit approval, present the results, then save the user's selected identity.
---

# Create character options

Read `../../shared/spend-policy.md` first. Use V6 MCP tools and keep the character batch tied to the active project.

1. Prepare an editable prompt from the approved source frame or user casting notes. Show it and let the user revise casting, wardrobe, setting, or style.
2. Call `characters_quote` with the exact payload planned for generation.
3. Show the model, image count, per-item and total estimated credits, and quote expiry. Ask the user for a fresh explicit `yes` in chat. Stop and wait.
4. After the user says yes, call `characters_generate` with the identical payload and quote's `approvalToken`. Do not put the token in the payload, a file, or a log.
5. Present all returned options together and wait for the user's choice. Character choice does not approve frame generation.
6. Save the selected character with `character_lock`, or use `character_use_saved` for an existing saved identity.

If the quote is missing or does not contain a usable credit estimate, stop. If generation fails, quote a retry and ask for a new `yes` before calling again.
