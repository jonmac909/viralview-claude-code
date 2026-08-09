---
name: search-library
description: Search Viral View's public ad library and return concise source-video candidates with IDs, titles, styles, durations, and preview URLs. Use when the user needs a viral ad reference, source video, creative style, or library candidate before cloning.
---

# Search the Viral View library

Run:

```bash
python3 skills/search-library/scripts/search_library.py --query "SEARCH" --limit 8
```

Add `--style STYLE` when the user names a visual style. Use `--cursor CURSOR` only to fetch the next page.

Present no more than eight candidates. Include ID, title, duration, style, thumbnail URL, and any available preview URL. Do not select for the user. Wait for a choice, then load the exact item with:

```bash
python3 scripts/viralview.py library-item --id ITEM_ID
```

Library search has no image or video generation call and does not require spend approval.
