# Agent Adam

An AI-powered personal life management assistant built with Streamlit and Anthropic's Claude API. Agent Adam acts as a motivational coach that helps manage your day-to-day schedule across personal, academic, and professional responsibilities through a single conversational interface.

## Features

- **Calendar Management** — View, create, and delete Google Calendar events through natural conversation
- **Email Access** — Read Gmail inbox, view unread messages, and mark emails as read
- **Task Management** — View, create, update status, and delete Google Tasks
- **Web Search** — Search the web for real-time information using DuckDuckGo
- **Live Dashboard** — Auto-refreshing sidebar showing today's schedule, 7-day outlook, important emails, and open tasks
- **Motivational Coaching** — Encouraging, proactive tone that celebrates wins, nudges about deadlines, and keeps you on track

## Tech Stack

- **Frontend**: Streamlit
- **LLM**: Anthropic Claude API (agentic tool-use loop)
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

## Future Plans

- Option to choose the LLM provider, including locally hosted models
- User-selectable integrations so you only enable the services you need
