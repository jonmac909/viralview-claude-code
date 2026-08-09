# Spend and approval policy

Every image or video generation batch is a paid action.

Before each batch:

1. Calculate the number of images or video scenes in the batch.
2. Read current usage and cost information with `$usage-costs`.
3. Show the model, item count, per-item estimate, and total estimated credits.
4. Ask for an explicit `yes` in the current chat.
5. Submit only that batch after the user replies `yes`.

Approval expires when the approved batch is submitted, changed, cancelled, or fails before submission. Regeneration, retry, a different model, a different item count, and the next pipeline stage each require a new estimate and a new `yes`.

Do not accept silence, a previous approval, setup completion, project approval, character selection, or scene-cut approval as permission to spend credits.

If the API cannot provide enough information to estimate credits, stop. Explain what is missing. Do not submit the batch.
