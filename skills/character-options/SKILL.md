---
name: character-options
description: Prepare a Viral View character prompt, generate a three-option character batch with a mandatory credit confirmation, present the images, and save the user's selected identity. Use when a clone needs a new character, a different spokesperson, or a reusable character choice.
---

# Create character options

Read `../../shared/spend-policy.md` first.

## Prepare the prompt

Build an editable prompt from the source frame:

```bash
python3 skills/character-options/scripts/character_options.py prepare --image-url URL
```

Show the prompt. Let the user change casting, wardrobe, setting, or style before spending credits.

## Generate three options

Read usage and estimate the complete three-image batch. Show the per-image and total credit estimate. Ask for an explicit `yes`.

After the user replies `yes`, run:

```bash
python3 skills/character-options/scripts/character_options.py generate \
  --prompt-file character-prompt.txt \
  --estimated-credits TOTAL \
  --confirm yes
```

The script submits exactly three distinct character models and polls their existing task IDs. Do not rerun failed options automatically.

Present all successful image URLs together. Wait for the user to pick one. Character selection is not permission to generate remake frames.

Save the selected candidate and build its lock before moving to frame generation.
