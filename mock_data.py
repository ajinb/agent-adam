"""
Mock data layer simulating Google Calendar, Gmail, and Notion-style tasks.
This serves as the prototype data source before real API integrations.
"""

import json
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Calendar events (simulates Google Calendar)
# ---------------------------------------------------------------------------

def _base_calendar():
    today = datetime.now().date()
    return [
        {
            "id": "cal-1",
            "title": "AIML-500 Lecture",
            "date": str(today),
            "start_time": "10:00",
            "end_time": "11:30",
            "location": "Online – Zoom",
            "description": "Machine Learning Fundamentals lecture",
            "calendar": "Coursework",
        },
        {
            "id": "cal-2",
            "title": "Gym – Upper Body",
            "date": str(today),
            "start_time": "17:00",
            "end_time": "18:00",
            "location": "Campus Rec Center",
            "description": "Upper body strength training",
            "calendar": "Personal",
        },
        {
            "id": "cal-3",
            "title": "Team Project Meeting",
            "date": str(today + timedelta(days=1)),
            "start_time": "14:00",
            "end_time": "15:00",
            "location": "Library Room 204",
            "description": "Sprint planning for capstone project",
            "calendar": "Coursework",
        },
        {
            "id": "cal-4",
            "title": "Grocery Shopping",
            "date": str(today + timedelta(days=1)),
            "start_time": "18:30",
            "end_time": "19:30",
            "location": "Trader Joe's",
            "description": "Weekly grocery run",
            "calendar": "Personal",
        },
        {
            "id": "cal-5",
            "title": "AI-1.4 Assignment Due",
            "date": str(today + timedelta(days=3)),
            "start_time": "23:59",
            "end_time": "23:59",
            "location": "",
            "description": "Submit chatbot + documentation",
            "calendar": "Deadlines",
        },
        {
            "id": "cal-6",
            "title": "Dentist Appointment",
            "date": str(today + timedelta(days=5)),
            "start_time": "09:00",
            "end_time": "10:00",
            "location": "Downtown Dental Clinic",
            "description": "Regular checkup",
            "calendar": "Personal",
        },
    ]


# ---------------------------------------------------------------------------
# Emails (simulates Gmail inbox)
# ---------------------------------------------------------------------------

def _base_emails():
    today = datetime.now().date()
    return [
        {
            "id": "email-1",
            "from": "prof.smith@iwu.edu",
            "subject": "AIML-500: Updated Rubric for AI-1.4",
            "date": str(today - timedelta(days=1)),
            "snippet": "Hi class, I've updated the rubric for the chatbot assignment. Please review the new criteria for documentation...",
            "read": False,
            "labels": ["Coursework", "Important"],
        },
        {
            "id": "email-2",
            "from": "teamlead@iwu.edu",
            "subject": "Re: Capstone – Meeting Agenda",
            "date": str(today - timedelta(days=1)),
            "snippet": "Here's the agenda for tomorrow's sprint planning: 1) Review backlog 2) Assign tasks 3) Set deadlines...",
            "read": True,
            "labels": ["Coursework"],
        },
        {
            "id": "email-3",
            "from": "notifications@notion.so",
            "subject": "You have 3 tasks due this week",
            "date": str(today),
            "snippet": "Reminder: You have tasks due soon in your 'School' workspace...",
            "read": False,
            "labels": ["Notifications"],
        },
        {
            "id": "email-4",
            "from": "mom@gmail.com",
            "subject": "Call me this weekend!",
            "date": str(today),
            "snippet": "Hey! Just checking in. Give me a call when you're free this weekend. Love you!",
            "read": False,
            "labels": ["Personal"],
        },
    ]


# ---------------------------------------------------------------------------
# Tasks (simulates Notion task database)
# ---------------------------------------------------------------------------

def _base_tasks():
    today = datetime.now().date()
    return [
        {
            "id": "task-1",
            "title": "Build AI chatbot prototype",
            "project": "AIML-500",
            "due_date": str(today + timedelta(days=3)),
            "priority": "High",
            "status": "In Progress",
            "notes": "Streamlit + Claude API. Need to finish mock data and UI.",
        },
        {
            "id": "task-2",
            "title": "Write Design Thinking documentation",
            "project": "AIML-500",
            "due_date": str(today + timedelta(days=3)),
            "priority": "High",
            "status": "Not Started",
            "notes": "Cover all 5 phases. Include screenshots of chatbot.",
        },
        {
            "id": "task-3",
            "title": "Read Chapter 7 – Neural Networks",
            "project": "AIML-500",
            "due_date": str(today + timedelta(days=5)),
            "priority": "Medium",
            "status": "Not Started",
            "notes": "",
        },
        {
            "id": "task-4",
            "title": "Prepare capstone presentation slides",
            "project": "Capstone",
            "due_date": str(today + timedelta(days=7)),
            "priority": "Medium",
            "status": "Not Started",
            "notes": "10-minute presentation. Focus on methodology.",
        },
        {
            "id": "task-5",
            "title": "Pay rent",
            "project": "Personal",
            "due_date": str(today + timedelta(days=2)),
            "priority": "High",
            "status": "Not Started",
            "notes": "Due on the 10th every month.",
        },
    ]


# ---------------------------------------------------------------------------
# In-memory data store (persists during a Streamlit session)
# ---------------------------------------------------------------------------

class DataStore:
    """Simple in-memory store that Streamlit session_state can hold."""

    def __init__(self):
        self.calendar = _base_calendar()
        self.emails = _base_emails()
        self.tasks = _base_tasks()
        self._next_cal_id = len(self.calendar) + 1
        self._next_task_id = len(self.tasks) + 1

    # -- Calendar helpers ---------------------------------------------------
    def get_events(self, date_str: str | None = None) -> list[dict]:
        if date_str:
            return [e for e in self.calendar if e["date"] == date_str]
        return self.calendar

    def add_event(self, title: str, date: str, start_time: str, end_time: str,
                  location: str = "", description: str = "", calendar: str = "Personal") -> dict:
        event = {
            "id": f"cal-{self._next_cal_id}",
            "title": title,
            "date": date,
            "start_time": start_time,
            "end_time": end_time,
            "location": location,
            "description": description,
            "calendar": calendar,
        }
        self.calendar.append(event)
        self._next_cal_id += 1
        return event

    def delete_event(self, event_id: str) -> bool:
        before = len(self.calendar)
        self.calendar = [e for e in self.calendar if e["id"] != event_id]
        return len(self.calendar) < before

    # -- Email helpers ------------------------------------------------------
    def get_emails(self, unread_only: bool = False) -> list[dict]:
        if unread_only:
            return [e for e in self.emails if not e["read"]]
        return self.emails

    def mark_email_read(self, email_id: str) -> bool:
        for e in self.emails:
            if e["id"] == email_id:
                e["read"] = True
                return True
        return False

    # -- Task helpers -------------------------------------------------------
    def get_tasks(self, status: str | None = None, project: str | None = None) -> list[dict]:
        results = self.tasks
        if status:
            results = [t for t in results if t["status"].lower() == status.lower()]
        if project:
            results = [t for t in results if t["project"].lower() == project.lower()]
        return results

    def add_task(self, title: str, project: str = "Personal", due_date: str = "",
                 priority: str = "Medium", notes: str = "") -> dict:
        task = {
            "id": f"task-{self._next_task_id}",
            "title": title,
            "project": project,
            "due_date": due_date,
            "priority": priority,
            "status": "Not Started",
            "notes": notes,
        }
        self.tasks.append(task)
        self._next_task_id += 1
        return task

    def update_task_status(self, task_id: str, new_status: str) -> bool:
        for t in self.tasks:
            if t["id"] == task_id:
                t["status"] = new_status
                return True
        return False

    def delete_task(self, task_id: str) -> bool:
        before = len(self.tasks)
        self.tasks = [t for t in self.tasks if t["id"] != task_id]
        return len(self.tasks) < before
