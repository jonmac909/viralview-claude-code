---
name: export-video
description: Retrieve a completed Viral View V6 export or start a new quote-approved export from the active project's approved scene videos.
---

# Export a video

Use `project_status` to confirm the project and existing final output. If an export is already complete, return its saved URL without starting another render.

For a new export:

1. Build the app's export payload from approved scene videos and current editor state.
2. Call `export_quote` with the exact payload planned for export.
3. Show estimated credits, items, seconds, and expiry. Ask for a fresh explicit `yes` in chat and wait.
4. After approval, call `export_start` with the identical payload and returned `approvalToken`. Never place the token in the body, a file, or a log.
5. Poll `export_status` using the same project until the job is complete or terminal.
6. Return the final URL. Call `export_download` with the same-origin `/api/uploads/...` path when the user asks for the file.

Do not export draft or unapproved scene variants. Do not start another export while a job is active. A retry or changed timeline needs a new quote and a new user `yes`.
