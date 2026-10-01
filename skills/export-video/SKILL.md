---
name: export-video
description: Retrieve a completed Viral View V6 export or start a non-credit render from the active project's approved scene videos.
---

# Export a video

Use `project_status` to confirm the project and existing final output. If an export is already complete, return its saved URL without starting another render.

For a new export:

1. Build the app's export payload from approved scene videos and current editor state.
2. Confirm the approved scene list and current editor state with the user. Export rendering does not spend provider credits, so there is no paid quote or approval token.
3. Call `export_start` with the app's export payload to start the render.
4. Poll `export_status` using the same project until the job is complete or terminal.
5. Return the final URL. Call `export_download` with the same-origin `/api/uploads/...` path when the user asks for the file.

Do not export draft or unapproved scene variants. Do not start another export while a job is active. Confirm any material timeline change with the user before starting a new render.
