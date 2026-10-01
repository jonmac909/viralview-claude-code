# Spend and approval policy

Every image or video generation batch is a paid action. Product cutouts, persisted paid retries, and automatic paid steps are also paid actions. Final stitch/export renders are non-credit render jobs and do not use the paid quote flow.

Before each batch:

1. Calculate the number of images or video scenes in the batch.
2. Read current usage and cost information with `$usage-costs`.
3. Show the model, item count, per-item estimate, and total estimated credits.
4. Ask for an explicit `yes` in the current chat.
5. Submit only that batch after the user replies `yes`.

Approval expires when the approved batch is submitted, changed, cancelled, or fails before submission. Regeneration, retry, a different model, a different item count, and the next pipeline stage each require a new estimate and a new `yes`.

Do not accept silence, a previous approval, setup completion, project approval, character selection, or scene-cut approval as permission to spend credits.

If the API cannot provide enough information to estimate credits, stop. Explain what is missing. Do not submit the batch.

## V6 quote tokens

For V6 MCP paid tools, call the matching `<step>_quote` tool first with the exact payload planned for dispatch. Show the returned model, item count, seconds where applicable, estimated credits, and quote expiry. Wait for the user to reply `yes` in the current chat. Only then call the paired paid tool with that identical payload and the quote's `approvalToken`.

The app binds the token to one user/key, project, action, and canonical payload. Never edit the payload after quoting, reuse a token for a retry or another batch, or return the token outside the tool call and quote result needed for the paired operation. A `402` approval error means no new dispatch should be attempted with that token; quote again and ask the user before retrying. The server's per-key daily cap is a backstop, not a replacement for explicit user approval.

For Auto, the quote is derived from the project's persisted next-step plan. Supply a stable `requestId` and the intended `workspacePath` to both `auto_quote` and `auto_start`; do not invent item lists. If the saved project changes, request a fresh quote and a new `yes`.

This policy applies to character generation, frame generation/remakes, scene video generation/regeneration, automatic paid steps, overlays, product cutouts, and persisted paid retries. Final export rendering through `export_start` does not require a provider-credit quote or paid approval token. Keep `--confirm-paid YES` as an additional local guard for paid calls made through `scripts/viralview.py`.
