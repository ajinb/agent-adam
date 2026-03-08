"""
Agent Adam — Personal Life Management Assistant
Streamlit UI with chat interface and sidebar dashboard.
Connected to Google Calendar, Gmail, and Google Tasks.
"""

import os
from datetime import datetime, timedelta

import streamlit as st
import anthropic
from dotenv import load_dotenv

from google_integration import GoogleDataStore, get_credentials, is_authenticated
from chatbot import chat

load_dotenv()

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Agent Adam",
    page_icon="🤖",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Google Auth
# ---------------------------------------------------------------------------
if "google_authenticated" not in st.session_state:
    st.session_state.google_authenticated = is_authenticated()

if not st.session_state.google_authenticated:
    st.title("🤖 Agent Adam")
    st.subheader("Connect your Google account to get started")
    st.info("This will open a browser window to sign in with Google and grant access to Calendar, Gmail, and Tasks.")
    if st.button("🔗 Connect Google Account", use_container_width=True):
        try:
            creds = get_credentials()
            st.session_state.google_creds = creds
            st.session_state.google_authenticated = True
            st.rerun()
        except Exception as e:
            st.error(f"Authentication failed: {e}")
    st.stop()

# Load credentials
if "google_creds" not in st.session_state:
    st.session_state.google_creds = get_credentials()

# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------
if "store" not in st.session_state:
    st.session_state.store = GoogleDataStore(st.session_state.google_creds)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ---------------------------------------------------------------------------
# API key handling
# ---------------------------------------------------------------------------
api_key = os.getenv("ANTHROPIC_API_KEY", "")

if not api_key:
    st.warning("Please set your `ANTHROPIC_API_KEY` in a `.env` file or enter it below.")
    api_key = st.text_input("Anthropic API Key", type="password")
    if not api_key:
        st.stop()

client = anthropic.Anthropic(api_key=api_key)

# ---------------------------------------------------------------------------
# Sidebar — Dashboard (auto-refreshes every 60s without rerunning the app)
# ---------------------------------------------------------------------------
@st.fragment(run_every="1m")
def sidebar_dashboard():
    """Sidebar fragment that refreshes data every 60 seconds independently."""
    store = GoogleDataStore(st.session_state.google_creds)
    # Update the shared store so chatbot also uses fresh data
    st.session_state.store = store
    today_str = datetime.now().strftime("%Y-%m-%d")

    # Today's schedule
    st.subheader("📅 Today's Schedule")
    try:
        today_events = store.get_events(today_str)
        if today_events:
            for ev in sorted(today_events, key=lambda x: x["start_time"]):
                st.markdown(f"**{ev['start_time']}** — {ev['title']}")
                if ev.get("location"):
                    st.caption(f"📍 {ev['location']}")
        else:
            st.caption("No events today — enjoy the free time!")
    except Exception as e:
        today_events = []
        st.caption(f"Could not load events: {e}")

    st.divider()

    # 7-day look ahead
    st.subheader("🗓️ Next 7 Days")
    try:
        upcoming_events = store.get_events()  # defaults to next 7 days
        # Exclude today's events (already shown above)
        upcoming_events = [ev for ev in upcoming_events if ev.get("date", "") > today_str]
        if upcoming_events:
            current_date = None
            for ev in sorted(upcoming_events, key=lambda x: (x.get("date", ""), x["start_time"])):
                ev_date = ev.get("date", "")
                if ev_date != current_date:
                    current_date = ev_date
                    try:
                        label = datetime.strptime(ev_date, "%Y-%m-%d").strftime("%a, %b %d")
                    except ValueError:
                        label = ev_date
                    st.markdown(f"**{label}**")
                st.caption(f"  {ev['start_time']} — {ev['title']}")
        else:
            st.caption("No upcoming events this week!")
    except Exception as e:
        st.caption(f"Could not load upcoming events: {e}")

    st.divider()

    # Important emails only
    st.subheader("📧 Important Emails")
    try:
        unread = store.get_emails(unread_only=True)
        important_unread = [
            em for em in unread
            if not any(skip in em.get("from", "").lower() for skip in [
                "noreply", "no-reply", "notifications@", "mailer-daemon",
                "newsletter", "promo", "marketing", "updates@",
            ])
        ]
        if important_unread:
            for em in important_unread[:5]:
                sender = em["from"]
                if "<" in sender:
                    sender = sender.split("<")[0].strip().strip('"')
                st.markdown(f"**{sender}**")
                st.caption(em["subject"])
        else:
            st.caption("No important unread emails! 🎉")
    except Exception as e:
        important_unread = []
        st.caption(f"Could not load emails: {e}")

    st.divider()

    # Open tasks
    st.subheader("✅ Open Tasks")
    try:
        all_tasks = store.get_tasks()
        open_tasks = [t for t in all_tasks if t["status"] != "Completed"]
        if open_tasks:
            for t in open_tasks:
                due = f" (due {t['due_date']})" if t.get("due_date") else ""
                st.caption(f"• {t['title']}{due}")
        else:
            st.caption("All tasks done! 🏆")
    except Exception as e:
        open_tasks = []
        st.caption(f"Could not load tasks: {e}")

    st.divider()

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.chat_history = []
        st.rerun()


with st.sidebar:
    st.title("🤖 Agent Adam")
    st.caption("Your personal life-management assistant")
    st.caption("📧 adamtheagent007@gmail.com")
    st.divider()
    sidebar_dashboard()

# ---------------------------------------------------------------------------
# Main chat area
# ---------------------------------------------------------------------------
st.title("💬 Chat with Agent Adam")
st.caption("Ask about your schedule, tasks, emails — or anything else!")

# Display chat history
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Welcome message
if not st.session_state.chat_history:
    with st.chat_message("assistant"):
        welcome = (
            "Hey there! 👋 I'm **Agent Adam**, your personal assistant!\n\n"
            "I'm connected to your Google Calendar, Gmail, and Tasks. "
            "The sidebar shows your live data and refreshes every minute.\n\n"
            "What would you like to tackle? I'm here to help you crush it! 💪"
        )
        st.markdown(welcome)

# Chat input
if prompt := st.chat_input("What's on your mind?"):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response_text, updated_messages = chat(
                    client=client,
                    messages=st.session_state.messages,
                    store=st.session_state.store,
                )
                st.session_state.messages = updated_messages
                st.markdown(response_text)
                st.session_state.chat_history.append({"role": "assistant", "content": response_text})
            except Exception as e:
                error_msg = f"Oops, something went wrong: {str(e)}"
                st.error(error_msg)
                st.session_state.chat_history.append({"role": "assistant", "content": error_msg})

    st.rerun()
