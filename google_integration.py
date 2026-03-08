"""
Google API integration — Calendar, Gmail, and Tasks.
Replaces mock_data.py with real Google Workspace data.
"""

import os
import json
import base64
import re
from datetime import datetime, timedelta
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Scopes required for Calendar, Gmail, and Tasks
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/tasks",
]

CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "credentials.json")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "token.json")


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def get_credentials() -> Credentials:
    """Get valid Google OAuth credentials, prompting login if needed."""
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"Missing {CREDENTIALS_FILE}. Download OAuth credentials from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return creds


def is_authenticated() -> bool:
    """Check if we have valid stored credentials."""
    if not os.path.exists(TOKEN_FILE):
        return False
    try:
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        if creds and creds.valid:
            return True
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())
            return True
    except Exception:
        return False
    return False


# ---------------------------------------------------------------------------
# Google Calendar
# ---------------------------------------------------------------------------

class GoogleCalendar:
    def __init__(self, creds: Credentials):
        self.service = build("calendar", "v3", credentials=creds)

    def get_events(self, date_str: str | None = None, max_results: int = 20) -> list[dict]:
        """Get calendar events. If date_str given (YYYY-MM-DD), get events for that day."""
        tz = "America/Denver"
        tz_offset = "-07:00"
        if date_str:
            time_min = f"{date_str}T00:00:00{tz_offset}"
            time_max = f"{date_str}T23:59:59{tz_offset}"
        else:
            now = datetime.now()
            time_min = now.strftime(f"%Y-%m-%dT%H:%M:%S{tz_offset}")
            time_max = (now + timedelta(days=7)).strftime(f"%Y-%m-%dT%H:%M:%S{tz_offset}")

        result = self.service.events().list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            timeZone=tz,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = []
        for item in result.get("items", []):
            start = item.get("start", {})
            end = item.get("end", {})
            events.append({
                "id": item["id"],
                "title": item.get("summary", "(No title)"),
                "date": start.get("date", start.get("dateTime", "")[:10]),
                "start_time": start.get("dateTime", "")[11:16] if "dateTime" in start else "All day",
                "end_time": end.get("dateTime", "")[11:16] if "dateTime" in end else "All day",
                "location": item.get("location", ""),
                "description": item.get("description", ""),
            })
        return events

    def add_event(self, title: str, date: str, start_time: str, end_time: str,
                  location: str = "", description: str = "") -> dict:
        """Create a new calendar event."""
        event_body = {
            "summary": title,
            "location": location,
            "description": description,
            "start": {
                "dateTime": f"{date}T{start_time}:00",
                "timeZone": "America/Denver",
            },
            "end": {
                "dateTime": f"{date}T{end_time}:00",
                "timeZone": "America/Denver",
            },
        }
        created = self.service.events().insert(calendarId="primary", body=event_body).execute()
        return {
            "id": created["id"],
            "title": title,
            "date": date,
            "start_time": start_time,
            "end_time": end_time,
            "location": location,
            "description": description,
        }

    def delete_event(self, event_id: str) -> bool:
        """Delete an event by ID."""
        try:
            self.service.events().delete(calendarId="primary", eventId=event_id).execute()
            return True
        except Exception:
            return False


# ---------------------------------------------------------------------------
# Gmail
# ---------------------------------------------------------------------------

class GoogleMail:
    def __init__(self, creds: Credentials):
        self.service = build("gmail", "v1", credentials=creds)

    def get_emails(self, unread_only: bool = False, max_results: int = 10) -> list[dict]:
        """Get emails from inbox."""
        query = "in:inbox"
        if unread_only:
            query += " is:unread"

        result = self.service.users().messages().list(
            userId="me", q=query, maxResults=max_results
        ).execute()

        emails = []
        for msg_meta in result.get("messages", []):
            msg = self.service.users().messages().get(
                userId="me", id=msg_meta["id"], format="metadata",
                metadataHeaders=["From", "Subject", "Date"]
            ).execute()

            headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
            labels = msg.get("labelIds", [])

            emails.append({
                "id": msg["id"],
                "from": headers.get("From", "Unknown"),
                "subject": headers.get("Subject", "(No subject)"),
                "date": headers.get("Date", ""),
                "snippet": msg.get("snippet", ""),
                "read": "UNREAD" not in labels,
                "labels": [l for l in labels if l not in ("INBOX", "UNREAD", "CATEGORY_PERSONAL", "CATEGORY_UPDATES", "CATEGORY_PROMOTIONS", "CATEGORY_SOCIAL")],
            })
        return emails

    def mark_email_read(self, email_id: str) -> bool:
        """Mark an email as read."""
        try:
            self.service.users().messages().modify(
                userId="me", id=email_id,
                body={"removeLabelIds": ["UNREAD"]}
            ).execute()
            return True
        except Exception:
            return False


# ---------------------------------------------------------------------------
# Google Tasks
# ---------------------------------------------------------------------------

class GoogleTasks:
    def __init__(self, creds: Credentials):
        self.service = build("tasks", "v1", credentials=creds)
        self._default_tasklist = None

    def _get_default_tasklist(self) -> str:
        """Get the default task list ID."""
        if self._default_tasklist:
            return self._default_tasklist
        result = self.service.tasklists().list(maxResults=1).execute()
        items = result.get("items", [])
        if items:
            self._default_tasklist = items[0]["id"]
        else:
            created = self.service.tasklists().insert(body={"title": "LifeCoach Tasks"}).execute()
            self._default_tasklist = created["id"]
        return self._default_tasklist

    def get_tasks(self, status: str | None = None, max_results: int = 20) -> list[dict]:
        """Get tasks from the default task list."""
        tl_id = self._get_default_tasklist()

        show_completed = True
        if status and status.lower() in ("not started", "in progress"):
            show_completed = False

        result = self.service.tasks().list(
            tasklist=tl_id,
            maxResults=max_results,
            showCompleted=show_completed,
            showHidden=show_completed,
        ).execute()

        tasks = []
        for item in result.get("items", []):
            task_status = "Completed" if item.get("status") == "completed" else "Not Started"
            # Check notes for "In Progress" marker
            notes = item.get("notes", "")
            if "IN_PROGRESS" in notes.upper():
                task_status = "In Progress"

            due = item.get("due", "")
            if due:
                due = due[:10]  # Extract YYYY-MM-DD

            task = {
                "id": item["id"],
                "title": item.get("title", "(No title)"),
                "due_date": due,
                "status": task_status,
                "notes": notes.replace("[IN_PROGRESS]", "").strip(),
            }
            tasks.append(task)

        if status:
            tasks = [t for t in tasks if t["status"].lower() == status.lower()]

        return tasks

    def add_task(self, title: str, due_date: str = "", priority: str = "Medium",
                 notes: str = "") -> dict:
        """Create a new task."""
        tl_id = self._get_default_tasklist()
        body = {"title": title}

        task_notes = notes
        if priority and priority != "Medium":
            task_notes = f"[Priority: {priority}] {task_notes}".strip()
        if task_notes:
            body["notes"] = task_notes

        if due_date:
            body["due"] = f"{due_date}T00:00:00.000Z"

        created = self.service.tasks().insert(tasklist=tl_id, body=body).execute()

        return {
            "id": created["id"],
            "title": title,
            "due_date": due_date,
            "priority": priority,
            "status": "Not Started",
            "notes": notes,
        }

    def update_task_status(self, task_id: str, new_status: str) -> bool:
        """Update a task's status."""
        tl_id = self._get_default_tasklist()
        try:
            task = self.service.tasks().get(tasklist=tl_id, task=task_id).execute()

            if new_status.lower() == "completed":
                task["status"] = "completed"
                # Remove IN_PROGRESS marker if present
                task["notes"] = task.get("notes", "").replace("[IN_PROGRESS]", "").strip()
            elif new_status.lower() == "in progress":
                task["status"] = "needsAction"
                notes = task.get("notes", "")
                if "[IN_PROGRESS]" not in notes:
                    task["notes"] = f"[IN_PROGRESS] {notes}".strip()
            else:  # Not Started
                task["status"] = "needsAction"
                task["notes"] = task.get("notes", "").replace("[IN_PROGRESS]", "").strip()

            self.service.tasks().update(tasklist=tl_id, task=task_id, body=task).execute()
            return True
        except Exception:
            return False

    def delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        tl_id = self._get_default_tasklist()
        try:
            self.service.tasks().delete(tasklist=tl_id, task=task_id).execute()
            return True
        except Exception:
            return False


# ---------------------------------------------------------------------------
# Unified DataStore (drop-in replacement for mock_data.DataStore)
# ---------------------------------------------------------------------------

class GoogleDataStore:
    """Wraps Google Calendar, Gmail, and Tasks into a unified interface
    matching the same API as the mock DataStore."""

    def __init__(self, creds: Credentials):
        self.calendar = GoogleCalendar(creds)
        self.mail = GoogleMail(creds)
        self.tasks = GoogleTasks(creds)

    # -- Calendar -----------------------------------------------------------
    def get_events(self, date_str: str | None = None) -> list[dict]:
        return self.calendar.get_events(date_str)

    def add_event(self, title: str, date: str, start_time: str, end_time: str,
                  location: str = "", description: str = "", calendar: str = "Personal") -> dict:
        return self.calendar.add_event(title, date, start_time, end_time, location, description)

    def delete_event(self, event_id: str) -> bool:
        return self.calendar.delete_event(event_id)

    # -- Email --------------------------------------------------------------
    def get_emails(self, unread_only: bool = False) -> list[dict]:
        return self.mail.get_emails(unread_only)

    def mark_email_read(self, email_id: str) -> bool:
        return self.mail.mark_email_read(email_id)

    # -- Tasks --------------------------------------------------------------
    def get_tasks(self, status: str | None = None, project: str | None = None) -> list[dict]:
        # Google Tasks doesn't have "project" — ignore that filter
        return self.tasks.get_tasks(status)

    def add_task(self, title: str, project: str = "Personal", due_date: str = "",
                 priority: str = "Medium", notes: str = "") -> dict:
        return self.tasks.add_task(title, due_date, priority, notes)

    def update_task_status(self, task_id: str, new_status: str) -> bool:
        return self.tasks.update_task_status(task_id, new_status)

    def delete_task(self, task_id: str) -> bool:
        return self.tasks.delete_task(task_id)
