---
name: export-video
description: Retrieve an existing Viral View project's finished video or submit and poll a final stitch export from approved scene videos. Use when the user asks for the final MP4, wants to re-export a project, or needs the download URL for a completed clone.
---

# Export a video

Check for an existing export first:

```bash
python3 skills/export-video/scripts/export_video.py fetch --project-id PROJECT_ID
```

If a finished `stitched_video_url` exists, return it without starting another render.

For a new export, build a JSON payload from approved scene videos and run:

```bash
python3 skills/export-video/scripts/export_video.py export --payload export.json --confirm-export YES
```

The script starts `/api/ugc/stitch-videos`, resumes an async job when returned, and prints the final MP4 URL. Do not export draft or unapproved scene variants. Do not start a second job while the first job ID is active.
