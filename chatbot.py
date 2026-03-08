"""
Core chatbot logic — Claude API with tool-use for calendar, email, tasks, and web search.
"""

import json
from datetime import datetime

import anthropic
from duckduckgo_search import DDGS

from mock_data import DataStore

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are **Agent Adam**, a personal life-management assistant with the energy of a motivational coach. You are connected to the user's real Google Calendar, Gmail, and Google Tasks.

## Your personality
- Warm, encouraging, and upbeat — but never fake
- Celebrate wins (even small ones like checking off a task)
- Gently nudge the user about upcoming deadlines or forgotten tasks
- Use short, punchy sentences when giving schedule summaries
- When the user seems stressed, acknowledge it and help prioritize

## Your capabilities
You help the user manage their day-to-day life across three areas:
1. **Google Calendar** — View, create, and delete real calendar events
2. **Gmail** — View inbox, check unread messages, mark as read
3. **Google Tasks** — View, create, update status, and delete tasks
4. **Web Search** — Look up information online when the user asks a question you can't answer from their data

## Rules
- Always check the user's calendar/tasks before giving schedule advice
- When creating events or tasks, confirm the details back to the user
- Never fabricate calendar events, emails, or tasks — only report what's in the data
- If the user asks about something outside your tools, use web search
- Keep responses concise — the user is busy!
- Use today's date for relative references (today, tomorrow, this week, etc.)
- Event and task IDs from Google are long strings — don't show them to the user, just use them internally

Today's date is: {today}
"""

# ---------------------------------------------------------------------------
# Tool definitions for Claude
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "get_calendar_events",
        "description": "Get calendar events. Optionally filter by a specific date (YYYY-MM-DD). Returns all events if no date is given.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Optional date filter in YYYY-MM-DD format"
                }
            },
            "required": []
        }
    },
    {
        "name": "add_calendar_event",
        "description": "Create a new calendar event.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Event title"},
                "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                "start_time": {"type": "string", "description": "Start time in HH:MM format"},
                "end_time": {"type": "string", "description": "End time in HH:MM format"},
                "location": {"type": "string", "description": "Event location (optional)"},
                "description": {"type": "string", "description": "Event description (optional)"},
                "calendar": {"type": "string", "description": "Calendar category: Personal, Coursework, or Deadlines"}
            },
            "required": ["title", "date", "start_time", "end_time"]
        }
    },
    {
        "name": "delete_calendar_event",
        "description": "Delete a calendar event by its ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "description": "The event ID to delete (e.g. 'cal-1')"}
            },
            "required": ["event_id"]
        }
    },
    {
        "name": "get_emails",
        "description": "Get emails from the inbox. Can filter to show only unread emails.",
        "input_schema": {
            "type": "object",
            "properties": {
                "unread_only": {"type": "boolean", "description": "If true, only return unread emails"}
            },
            "required": []
        }
    },
    {
        "name": "mark_email_read",
        "description": "Mark a specific email as read by its ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "email_id": {"type": "string", "description": "The email ID to mark as read (e.g. 'email-1')"}
            },
            "required": ["email_id"]
        }
    },
    {
        "name": "get_tasks",
        "description": "Get tasks from the task list. Optionally filter by status or project.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Filter by status: 'Not Started', 'In Progress', or 'Completed'"},
                "project": {"type": "string", "description": "Filter by project name (e.g. 'AIML-500', 'Personal')"}
            },
            "required": []
        }
    },
    {
        "name": "add_task",
        "description": "Create a new task.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Task title"},
                "project": {"type": "string", "description": "Project name (e.g. 'AIML-500', 'Personal')"},
                "due_date": {"type": "string", "description": "Due date in YYYY-MM-DD format"},
                "priority": {"type": "string", "description": "Priority: High, Medium, or Low"},
                "notes": {"type": "string", "description": "Additional notes"}
            },
            "required": ["title"]
        }
    },
    {
        "name": "update_task_status",
        "description": "Update the status of an existing task.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "The task ID (e.g. 'task-1')"},
                "new_status": {"type": "string", "description": "New status: 'Not Started', 'In Progress', or 'Completed'"}
            },
            "required": ["task_id", "new_status"]
        }
    },
    {
        "name": "delete_task",
        "description": "Delete a task by its ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "The task ID to delete (e.g. 'task-1')"}
            },
            "required": ["task_id"]
        }
    },
    {
        "name": "web_search",
        "description": "Search the web for information using DuckDuckGo. Use this when the user asks questions you can't answer from their calendar, email, or tasks.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"}
            },
            "required": ["query"]
        }
    },
]

# ---------------------------------------------------------------------------
# Tool execution
# ---------------------------------------------------------------------------

def execute_tool(tool_name: str, tool_input: dict, store: DataStore) -> str:
    """Execute a tool call and return the result as a JSON string."""
    try:
        if tool_name == "get_calendar_events":
            result = store.get_events(tool_input.get("date"))
        elif tool_name == "add_calendar_event":
            result = store.add_event(
                title=tool_input["title"],
                date=tool_input["date"],
                start_time=tool_input["start_time"],
                end_time=tool_input["end_time"],
                location=tool_input.get("location", ""),
                description=tool_input.get("description", ""),
                calendar=tool_input.get("calendar", "Personal"),
            )
        elif tool_name == "delete_calendar_event":
            success = store.delete_event(tool_input["event_id"])
            result = {"deleted": success, "event_id": tool_input["event_id"]}
        elif tool_name == "get_emails":
            result = store.get_emails(tool_input.get("unread_only", False))
        elif tool_name == "mark_email_read":
            success = store.mark_email_read(tool_input["email_id"])
            result = {"marked_read": success, "email_id": tool_input["email_id"]}
        elif tool_name == "get_tasks":
            result = store.get_tasks(
                status=tool_input.get("status"),
                project=tool_input.get("project"),
            )
        elif tool_name == "add_task":
            result = store.add_task(
                title=tool_input["title"],
                project=tool_input.get("project", "Personal"),
                due_date=tool_input.get("due_date", ""),
                priority=tool_input.get("priority", "Medium"),
                notes=tool_input.get("notes", ""),
            )
        elif tool_name == "update_task_status":
            success = store.update_task_status(tool_input["task_id"], tool_input["new_status"])
            result = {"updated": success, "task_id": tool_input["task_id"], "new_status": tool_input["new_status"]}
        elif tool_name == "delete_task":
            success = store.delete_task(tool_input["task_id"])
            result = {"deleted": success, "task_id": tool_input["task_id"]}
        elif tool_name == "web_search":
            result = _web_search(tool_input["query"])
        else:
            result = {"error": f"Unknown tool: {tool_name}"}
    except Exception as e:
        result = {"error": str(e)}

    return json.dumps(result, default=str)


def _web_search(query: str, max_results: int = 5) -> list[dict]:
    """Perform a DuckDuckGo web search."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return [{"title": r["title"], "url": r["href"], "snippet": r["body"]} for r in results]
    except Exception as e:
        return [{"error": f"Search failed: {str(e)}"}]


# ---------------------------------------------------------------------------
# Chat function (agentic loop with tool use)
# ---------------------------------------------------------------------------

def chat(client: anthropic.Anthropic, messages: list[dict], store: DataStore,
         model: str = "claude-sonnet-4-20250514") -> tuple[str, list[dict]]:
    """
    Send messages to Claude with tools. Handles the tool-use loop.
    Returns (final_text_response, updated_messages).
    """
    system = SYSTEM_PROMPT.format(today=datetime.now().strftime("%A, %B %d, %Y"))

    response = client.messages.create(
        model=model,
        max_tokens=1024,
        system=system,
        tools=TOOLS,
        messages=messages,
    )

    # Agentic loop: keep going while Claude wants to use tools
    while response.stop_reason == "tool_use":
        # Build assistant message content
        assistant_content = response.content

        # Process all tool uses in this response
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                tool_result = execute_tool(block.name, block.input, store)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": tool_result,
                })

        # Append assistant message and tool results
        messages.append({"role": "assistant", "content": assistant_content})
        messages.append({"role": "user", "content": tool_results})

        # Call Claude again with tool results
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            system=system,
            tools=TOOLS,
            messages=messages,
        )

    # Extract final text response
    final_text = ""
    for block in response.content:
        if hasattr(block, "text"):
            final_text += block.text

    # Append final assistant response
    messages.append({"role": "assistant", "content": response.content})

    return final_text, messages
