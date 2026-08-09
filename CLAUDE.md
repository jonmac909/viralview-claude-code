# Viral View for Claude Code

Read `AGENTS.md` first. It contains the skill index, API rules, security boundary, and mandatory spend-confirmation policy.

Project skills live under `skills/`. When a request matches one, read that skill's `SKILL.md` before acting. Use only `scripts/viralview.py` for Viral View API calls.

An explicit `yes` must come from the user in the current chat before every paid image or video generation batch. Show the estimated credits first. Never infer approval or reuse an earlier approval.
