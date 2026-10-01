# Contributing

This is the Actionable AI (A²I) product repository, not an upstream template. Thanks for helping ship it.

## How we work

1. Read [task.md](./actionable-ai/docs/task.md) before starting. Work **one slice at a time**. The “Next up” block is the only implementation target unless you agree otherwise.
2. Architecture is locked: frontend [Option A](./actionable-ai/docs/5_Development_and_Execution/05_Frontend_Architecture.md), backend [Option B](./actionable-ai/docs/5_Development_and_Execution/06_Backend_Architecture.md). Do not introduce a second FastAPI app, put the widget inside `frontend/src`, or grow the old single `models.py` file.
3. Staging vs production policy lives in [07 Deployment Strategy](./actionable-ai/docs/5_Development_and_Execution/07_Deployment_Strategy.md). Do not re-open FastAPI Cloud as the primary host in a drive-by PR.

Local setup: [development.md](./development.md).

## Pull requests

- Keep the PR to one reviewable change (the current task slice, a bug, or docs).
- Tests should pass (`uv run bash scripts/test.sh` in `backend/`; Playwright when UI is involved).
- Do not add dependencies without saying why. Prefer not to touch `pyproject.toml` / `uv.lock` / `bun.lock` unless the slice needs it.
- Do not commit `.env`, secrets, or production dumps.

## Automated and AI-assisted changes

Use whatever tools help you work. The change still needs a human who understands the product and can defend the diff.

If the effort to write the prompt is less than the effort to review the result, do not open the PR. Do not paste raw LLM output into descriptions or comments.

## Questions

Ask in the team channel or on the PR. Product decisions belong in `actionable-ai/docs/`, not in a comment thread that will rot.
