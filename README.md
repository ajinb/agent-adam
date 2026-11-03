# Agent Adam

An AI-powered personal life management assistant built with Streamlit and Anthropic's Claude API. Agent Adam acts as a motivational coach that helps manage your day-to-day schedule across personal, academic, and professional responsibilities through a single conversational interface.

## Features

- **Calendar Management** — View, create, and delete Google Calendar events through natural conversation
- **Email Access** — Read your Gmail inbox and unread messages (read-only by default; set `AGENT_ADAM_GMAIL_WRITE=1` to also mark messages as read)
- **Task Management** — View, create, update status, and delete Google Tasks
- **Web Search** — Search the web for real-time information using DuckDuckGo
- **Live Dashboard** — Auto-refreshing sidebar showing today's schedule, 7-day outlook, important emails, and open tasks
- **Motivational Coaching** — Encouraging, proactive tone that celebrates wins, nudges about deadlines, and keeps you on track

## Tech Stack

- **Frontend**: Streamlit
- **LLM**: Anthropic Claude API (agentic tool-use loop; `claude-sonnet-5-5` by default, prompt caching, server-side refusal fallback)
- **Integrations**: Google Calendar, Gmail, Google Tasks, DuckDuckGo Search
- **Language**: Python

## Architecture

Agent Adam uses an agentic tool-use loop where Claude autonomously decides which Google APIs to call based on your natural language request. The app defines structured tool schemas for each integration, allowing Claude to chain multiple API calls to fulfill complex requests (e.g., "What's on my calendar today and do I have any unread emails?").

## Setup

1. Clone the repo and create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your API key using one of the following methods:
   - **Environment variable**: Copy `.env.example` to `.env` and add your Anthropic API key
   - **In-app input**: If no key is found, the app will prompt you to enter it via a password field

4. Set up Google OAuth credentials:
   - Create a project in Google Cloud Console and enable the Calendar, Gmail, and Tasks APIs
   - Download your OAuth 2.0 credentials as `credentials.json` and place it in the project root
   - On first run, you'll be prompted to authenticate via browser

5. Run the app:
   ```bash
   streamlit run app.py
   ```

### Docker

```bash
docker build -t agent-adam .
docker run -p 8501:8501 --env-file .env \
  -v "$PWD/credentials.json:/app/credentials.json:ro" agent-adam
```

## Security model

| Concern | How it is handled |
|---|---|
| Google OAuth refresh token | Stored in the OS keychain (macOS Keychain, Windows Credential Manager, Secret Service) via `keyring`; falls back to `token.json` written owner-only (0600). An old plaintext `token.json` is migrated into the keychain and deleted. `AGENT_ADAM_TOKEN_STORE=keyring\|file\|auto` |
| OAuth scopes | Calendar, Tasks, and **read-only** Gmail. `AGENT_ADAM_GMAIL_WRITE=1` swaps in `gmail.modify` (label changes such as mark-as-read; it cannot send or permanently delete). Re-authenticate after changing it. |
| Destructive actions | Deleting events or tasks is queued for your approval in the UI; the model can request it but never perform it. |
| Prompt injection | Email bodies and web results are fenced as untrusted content the model must not obey. |
| Runaway cost | The tool loop is capped at 10 round trips per turn. |

CI runs ruff, Bandit, pip-audit and the test suite on every push; CodeQL and OpenSSF Scorecard
run weekly. Report vulnerabilities privately via [GitHub security advisories](https://github.com/ajinb/agent-adam/security/advisories/new).

## Future Plans

- Option to choose the LLM provider, including locally hosted models
- User-selectable integrations so you only enable the services you need
