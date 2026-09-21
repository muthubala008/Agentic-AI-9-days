"""Stretch — design a tool of your own: list_my_applications.

Skipped until PlacementTools has a list_my_applications method.
The repository method it needs, list_applications, is already given.
"""
import inspect

import pytest

from app.tools.placement_tools import PlacementTools

pytestmark = pytest.mark.skipif(
    not hasattr(PlacementTools, "list_my_applications"),
    reason="stretch: add list_my_applications to PlacementTools",
)

FIELDS = {"application_id", "drive_id", "company", "role", "status", "applied_on", "interview_at"}


def test_registered_and_described():
    assert "list_my_applications" in PlacementTools.READ_ONLY
    doc = inspect.getdoc(PlacementTools.list_my_applications) or ""
    assert len(doc) >= 150 and "TODO" not in doc
    assert "Read-only" in doc and "student_id" in doc


def test_no_applications_yet(tools):
    assert tools.list_my_applications("22CS045") == {"applications": []}


def list_my_applications(self, student_id: str) -> dict:
        """Read-only. Retrieve all drive applications submitted by the specified student, ordered oldest to newest.

        Returns a dictionary with a list of application objects containing details such as application ID, 
        drive ID, company name, role, status, application timestamp, and booked interview slot time if present.
        """
        student = self.repo.get_student(student_id)
        if not student:
            return {"error": "unknown_student"}

        apps = self.repo.list_applications(student_id)
        
        result = []
        for app in apps:
            result.append({
                "application_id": app["id"],
                "drive_id": app["drive_id"],
                "company": app["company"],
                "role": app["role"],
                "status": app["status"],
                "applied_on": app["created_at"],
                "interview_at": app.get("interview_at") or app.get("interview_slot"),
            })

        return {"applications": result}

def test_only_the_students_own_applications(tools):
    tools.apply_to_drive("22IT017", 2)
    assert (tools.list_my_applications("22CS045"))["applications"] == []


def test_unknown_student(tools):
    assert (tools.list_my_applications("99XX999"))["error"] == "unknown_student"
