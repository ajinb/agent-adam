# Contributing

Thanks for helping improve Agent Adam.

## Development setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q            # offline; no API key or Google account needed
ruff check .
bandit -q -r . -x ./tests,./.venv -ll
```

## Design rules

- **Least privilege.** New features must not widen OAuth scopes by default. Write access is
  opt-in (see `AGENT_ADAM_GMAIL_WRITE`).
- **Destructive tools are queued, never executed by the model.** Anything that deletes data goes
  through `DESTRUCTIVE_TOOLS` and the approval UI.
- **Third-party text is data.** Results from email or the web are wrapped as untrusted content.
- **Secrets stay out of the repo and out of logs.** Tokens live in the OS keychain.

## Pull requests

Keep PRs focused, add a test for behaviour changes, and make sure CI is green.
