---
name: remix-script
description: Rewrite a Viral View source script for a target product, edit dialogue by scene, and flag lines that exceed or underfill the speaking-time budget. Use when adapting ad dialogue, changing a hook or CTA, fitting a line to a scene, or reviewing script timing before video generation.
---

# Remix a script

Prepare the current scenes, dialogue map, target product, and rewrite mode in a JSON file. Check timing before calling the API:

```bash
python3 skills/remix-script/scripts/remix_script.py check --payload rewrite.json
```

Use 3.2 to 4.4 spoken words per second as the warning range. A warning is not permission to truncate a sentence. Keep complete sentences and preserve the final CTA unless the user changes it.

Submit the approved rewrite request:

```bash
python3 skills/remix-script/scripts/remix_script.py rewrite --payload rewrite.json
```

Show the returned dialogue scene by scene and rerun the timing check. Wait for the user's script approval before any image or video generation.
