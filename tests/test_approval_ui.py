"""The approval queue as the user sees it (issue #25)."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).parent.parent / "app.py")


class Store:
    delete_result = True

    def __init__(self, _creds):
        pass

    def delete_task(self, task_id):
        return self.delete_result

    def get_events(self, date=None):
        return []

    def get_emails(self, unread_only=False):
        return []

    def get_tasks(self, status=None, project=None):
        return []


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "t")
    monkeypatch.setattr("google_integration.is_authenticated", lambda: True)
    monkeypatch.setattr("google_integration.get_credentials", object)
    monkeypatch.setattr("google_integration.GoogleDataStore", Store)
    at = AppTest.from_file(APP, default_timeout=30)
    at.session_state["pending_actions"] = [
        {"tool": "delete_task", "input": {"task_id": "t1"}, "summary": "Delete task t1"},
    ]
    return at.run()


def test_failed_delete_stays_queued_and_says_so(app, monkeypatch):
    monkeypatch.setattr(Store, "delete_result", False)

    app.button(key="approve_0").click().run()

    assert len(app.session_state["pending_actions"]) == 1
    assert "still waiting for you" in app.error[0].value
    assert not app.success


def test_successful_delete_leaves_the_queue_and_says_so(app):
    app.button(key="approve_0").click().run()

    assert app.session_state["pending_actions"] == []
    assert app.success[0].value == "Done: Delete task t1"


def test_the_outcome_is_shown_only_once(app):
    app.button(key="approve_0").click().run()
    app.run()

    assert not app.success
