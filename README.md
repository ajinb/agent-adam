# Agent Adam

An AI-powered personal life management assistant built with Streamlit and Anthropic's Claude API. Agent Adam acts as a motivational coach that helps manage your day-to-day schedule across personal, academic, and professional responsibilities.

## Features

- **Calendar Management** — View, create, and manage Google Calendar events through natural conversation
- **Email Access** — Read and summarize Gmail messages
- **Web Search** — Search the web for real-time information using DuckDuckGo
- **Motivational Coaching** — Encouraging, proactive tone that celebrates completed tasks and keeps you on track

## Tech Stack

- **Frontend**: Streamlit
- **LLM**: Anthropic Claude API
- **Integrations**: Google Calendar, Gmail, DuckDuckGo Search
- **Language**: Python

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

3. Create a `.env` file based on `.env.example` and add your Anthropic API key.

4. Run the app:
   ```bash
   streamlit run app.py
   ```
