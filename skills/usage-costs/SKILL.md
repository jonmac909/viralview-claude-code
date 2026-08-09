---
name: usage-costs
description: Read recent Viral View generation usage, summarize local API activity, and forecast image or video batch credits from known per-item cost data. Use before every paid generation batch, when the user asks about spend or balance, or when a retry needs a fresh estimate.
---

# Check usage and forecast spend

Read recent server usage and the local request log:

```bash
python3 skills/usage-costs/scripts/usage_costs.py recent
```

Forecast a batch only with a known per-item credit cost:

```bash
python3 skills/usage-costs/scripts/usage_costs.py forecast \
  --kind video \
  --model MODEL \
  --count 6 \
  --credits-per-item COST
```

Show the model, item count, per-item credits, total estimated credits, and available balance when present.

If the API does not provide a usable cost basis and no current public cost is supplied, report the estimate as unavailable and block generation. Never guess a credit amount.

After showing a valid estimate, ask for an explicit `yes`. The approval applies only to the exact batch that was estimated.
