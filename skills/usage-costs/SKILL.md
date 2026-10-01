---
name: usage-costs
description: Read recent Viral View usage and balance, then use the V6 quote tools to estimate the exact paid image, video, or automatic batch before requesting approval.
---

# Check usage and quote spend

Read recent server usage with `account_usage` and the available balance with `account_balance` when useful. Never forecast provider credits from guesses or stale per-item prices.

Before every paid batch, call the matching quote tool: `characters_quote`, `frames_quote`, `videos_quote`, or `auto_quote`. Show the model, item count, seconds, estimated credits, and expiry returned by the quote. Ask for a fresh explicit `yes` in chat and wait before calling its paid partner. Final export rendering is non-credit and does not have a quote tool.

Pass the same payload and quote `approvalToken` to the paid tool. Keep the token only in the calls. A changed batch, retry, regeneration, next pipeline step, or expired token requires a new quote and a new `yes`.
