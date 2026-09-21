import operator
from datetime import datetime, timezone

from app.domain import AlreadyApplied, Rule, Student
from app.data import InMemoryPlacementRepo
from app.tools.dispatch import dispatch

OPS = {
    ">=": operator.ge,
    "<=": operator.le,
    "==": operator.eq,
    "in": lambda actual, allowed: actual in allowed.split(","),
}


def _passes(rule: Rule, student_value) -> bool:
    return OPS[rule.op](student_value, rule.typed_value())


def _unknown_student(roll_no: str) -> dict:
    return {
        "error": "unknown_student",
        "hint": f"No student with roll number {roll_no!r}. Ask the user for their roll number, e.g. 22CS045.",
    }


def _unknown_drive(drive_id: int) -> dict:
    return {
        "error": "unknown_drive",
        "hint": f"No drive with id {drive_id}. Call list_open_drives to get valid ids.",
    }


class PlacementTools:
    """Every method named in TOOL_NAMES is exposed to the model. Its docstring IS the prompt.

    Two tools are complete samples: check_eligibility (read-only) and apply_to_drive (side effect).
    Copy their patterns for the tools marked TODO.
    """

    READ_ONLY = ("list_open_drives", "get_student", "check_eligibility", "list_my_applications","check_student_eligibility","get_drive_details")
    SIDE_EFFECTS = ("apply_to_drive", "book_interview_slot", "notify_student")
    TOOL_NAMES = READ_ONLY + SIDE_EFFECTS

    def __init__(self, repo: InMemoryPlacementRepo, notifier, clock=lambda: datetime.now(timezone.utc)):
        self.repo = repo
        self.notifier = notifier
        self.clock = clock

    def functions(self) -> dict:
        return {name: getattr(self, name) for name in self.TOOL_NAMES}

    def call(self, name: str, args: dict) -> dict:
        return dispatch(self.functions(), name, args)

    # ================================================================== SAMPLE 1 (given): read-only

    def _evaluate(self, s: Student, drive_id: int) -> list[dict]:
        failed = []
        for rule in self.repo.rules_for_drive(drive_id):
            actual = getattr(s, rule.field)
            if not _passes(rule, actual):
                failed.append({"rule_id": rule.id, "rule": str(rule), "actual": actual})
        return failed

    def check_eligibility(self, student_id: str, drive_id: int) -> dict:
        """Decide whether ONE student may apply to ONE drive, using the drive's eligibility rules.

        Use before apply_to_drive, or when the user asks "can I apply", "am I eligible for
        <company>", or "why can't I apply". Do NOT use to find drives; use list_open_drives.
        Read-only: changes nothing.

        Args:
            student_id: Roll number, e.g. "22CS045".
            drive_id: Integer id returned by list_open_drives. Never a company name.

        Returns:
            {"student_id", "drive_id", "eligible", "failed_rules": [{"rule_id", "rule", "actual"}]}.
            Explain every failed rule to the user; do not invent rules that are not listed.
        """
        s = self.repo.get_student(student_id)
        if s is None:
            return _unknown_student(student_id)
        if self.repo.get_drive(drive_id) is None:
            return _unknown_drive(drive_id)
        failed = self._evaluate(s, drive_id)
        return {
            "student_id": s.roll_no,
            "drive_id": drive_id,
            "eligible": not failed,
            "failed_rules": failed,
        }

    # ================================================================== SAMPLE 2 (given): side effect

    def apply_to_drive(self, student_id: str, drive_id: int) -> dict:
        """Submit a placement application for ONE student to ONE drive.

        Side effect: creates an application record the placement cell will act on. Call it only
        when the user clearly asks to apply or register ("apply me", "sign me up"), never to
        check or explore. Eligibility is re-checked here, but call check_eligibility first so
        you can explain the result.

        Args:
            student_id: Roll number, e.g. "22CS045".
            drive_id: Integer id returned by list_open_drives.

        Returns:
            {"application_id", "student_id", "drive_id", "status": "applied",
             "available_slots": [{"slot_id", "starts_at"}]}. Offer the slots to the user;
            book one only when they choose.
        """
        s = self.repo.get_student(student_id)
        if s is None:
            return _unknown_student(student_id)
        d = self.repo.get_drive(drive_id)
        if d is None:
            return _unknown_drive(drive_id)
        if d.status != "open" or d.deadline <= self.clock():
            return {
                "error": "drive_closed",
                "hint": f"{d.company} is not accepting applications. Call list_open_drives for open ones.",
            }
        failed = self._evaluate(s, drive_id)
        if failed:
            return {
                "error": "not_eligible",
                "failed_rules": failed,
                "hint": "Explain the failed rules to the user. Do not retry.",
            }
        try:
            application_id = self.repo.create_application(s.id, drive_id)
        except AlreadyApplied:
            return {
                "error": "already_applied",
                "hint": "The student has already applied to this drive. Tell the user; do not retry.",
            }
        slots = self.repo.free_slots(drive_id)
        return {
            "application_id": application_id,
            "student_id": s.roll_no,
            "drive_id": drive_id,
            "status": "applied",
            "available_slots": [
                {"slot_id": sl.id, "starts_at": sl.starts_at.isoformat()} for sl in slots
            ],
        }

    # ================================================================== YOUR TOOLS

    def get_student(self, student_id: str) -> dict:
        """Fetch profile information for ONE student.

        Use when you need the student's details like CGPA, branch, backlogs, or graduation year.
        Read-only: changes nothing.

        Args:
            student_id: Roll number, e.g. "22CS045".

        Returns:
            {"student_id", "name", "branch", "cgpa", "backlogs", "grad_year"}.
        """
        s = self.repo.get_student(student_id)
        if s is None:
            return _unknown_student(student_id)
        return {
            "student_id": s.roll_no,
            "name": s.name,
            "branch": s.branch,
            "cgpa": s.cgpa,
            "backlogs": s.backlogs,
            "grad_year": s.grad_year,
        }

    def list_open_drives(self, branch: str | None = None, grad_year: int | None = None) -> dict:
        """List active placement drives accepting applications.

        Use when the user asks "what drives are open", "show available placement drives", or
        to locate drive IDs before checking eligibility. Read-only: changes nothing.

        Args:
            branch: Optional branch name filter, e.g. "CSE".
            grad_year: Optional graduation year filter, e.g. 2026.

        Returns:
            {"drives": [{"drive_id", "company", "role", "ctc_lpa", "deadline"}]}.
        """
        open_drives = self.repo.list_open_drives(self.clock())
        matching_drives = []

        for d in open_drives:
            rules = self.repo.rules_for_drive(d.id)
            skip = False

            if branch is not None:
                branch_rules = [r for r in rules if r.field == "branch"]
                for r in branch_rules:
                    if not _passes(r, branch):
                        skip = True
                        break

            if grad_year is not None and not skip:
                grad_rules = [r for r in rules if r.field == "grad_year"]
                for r in grad_rules:
                    if not _passes(r, grad_year):
                        skip = True
                        break

            if not skip:
                matching_drives.append({
                    "drive_id": d.id,
                    "company": d.company,
                    "role": d.role,
                    "ctc_lpa": d.ctc_lpa,
                    "deadline": d.deadline.strftime("%Y-%m-%d"),
                })

        return {"drives": matching_drives}

    def book_interview_slot(self, student_id: str, slot_id: int) -> dict:
        """Reserve an interview slot for an application.

        Side effect: claims an open interview slot for the student. Call only when the user
        explicitly requests to book or select a specific slot.

        Args:
            student_id: Roll number, e.g. "22CS045".
            slot_id: Integer ID of an available slot.

        Returns:
            {"slot_id", "drive_id", "starts_at", "status": "booked"}.
        """
        s = self.repo.get_student(student_id)
        if s is None:
            return _unknown_student(student_id)

        slot = self.repo.get_slot(slot_id)
        if slot is None:
            return {
                "error": "unknown_slot",
                "hint": f"No slot with id {slot_id}. Verify available slots for the drive.",
            }

        if not self.repo.has_application(s.id, slot.drive_id):
            return {
                "error": "no_application",
                "hint": "The student has not applied to this drive yet. Call apply_to_drive first.",
            }

        booked = self.repo.claim_slot(slot_id, s.id)
        if not booked:
            free_slots = self.repo.free_slots(slot.drive_id)
            return {
                "error": "slot_taken",
                "hint": "That slot was already booked by another candidate.",
                "available_slots": [
                    {"slot_id": sl.id, "starts_at": sl.starts_at.isoformat()} for sl in free_slots
                ],
            }

        return {
            "slot_id": slot.id,
            "drive_id": slot.drive_id,
            "starts_at": slot.starts_at.isoformat(),
            "status": "booked",
        }

    def notify_student(self, student_id: str, message: str) -> dict:
        """Send an urgent placement notification SMS/alert to the student.

        Side effect: dispatches an asynchronous message via the placement notification gateway.

        Args:
            student_id: Roll number, e.g. "22CS045".
            message: Text message up to 160 characters.

        Returns:
            {"notification_id", "status": "queued"}.
        """
        s = self.repo.get_student(student_id)
        if s is None:
            return _unknown_student(student_id)

        if not message or len(message) > 160:
            return {
                "error": "invalid_message",
                "hint": "Message must be non-empty and at most 160 characters long.",
            }

        notification_id = self.notifier.send(student_id, message)
        return {"notification_id": notification_id, "status": "queued"}

    def list_my_applications(self, student_id: str) -> dict:
        """List all placement drive applications submitted by a student.

        Use when the student asks "where have I applied", "check my applications", or
        "when is my interview". Read-only: changes nothing.

        Args:
            student_id: Roll number, e.g. "22CS045".

        Returns:
            {"applications": [{"application_id", "drive_id", "company", "role", "status", "created_at", "interview_at"}]}.
        """
        s = self.repo.get_student(student_id)
        if s is None:
            return _unknown_student(student_id)

        apps = self.repo.list_applications(s.id)
        formatted_apps = []
        for app in apps:
            formatted_apps.append({
                "application_id": app["application_id"],
                "drive_id": app["drive_id"],
                "company": app["company"],
                "role": app["role"],
                "status": app["status"],
                "created_at": app["created_at"].isoformat() if isinstance(app["created_at"], datetime) else app["created_at"],
                "interview_at": app["interview_at"].isoformat() if isinstance(app["interview_at"], datetime) else app["interview_at"],
            })

        return {"applications": formatted_apps}
    def get_drive_details(self, drive_id: int) -> dict:
        """Get detailed information about ONE placement drive.

        Use when the user asks for details about a specific drive/company,
        such as eligibility rules, role, package, deadline, or interview slots.
        Read-only: changes nothing.

        Args:
            drive_id: Integer id returned by list_open_drives. Never a company name.

        Returns:
            {
                "drive_id",
                "company",
                "role",
                "ctc_lpa",
                "deadline",
                "status",
                "eligibility_rules"
            }.
        """
        d = self.repo.get_drive(drive_id)

        if d is None:
            return _unknown_drive(drive_id)

        rules = self.repo.rules_for_drive(drive_id)

        return {
            "drive_id": d.id,
            "company": d.company,
            "role": d.role,
            "ctc_lpa": d.ctc_lpa,
            "deadline": d.deadline.isoformat(),
            "status": d.status,
            "eligibility_rules": [
                {
                    "rule_id": rule.id,
                    "rule": str(rule),
                }
                for rule in rules
            ],
        }


    def check_student_eligibility(self, student_id: str, drive_id: int) -> dict:
        """Check whether ONE student is eligible for ONE placement drive.

        Use when the user asks whether they can apply to a particular drive.
        Read-only: changes nothing.

        Args:
            student_id: Roll number, e.g. "22CS045".
            drive_id: Integer id returned by list_open_drives.

        Returns:
            {"student_id", "drive_id", "eligible", "failed_rules"}.
        """
        return self.check_eligibility(student_id, drive_id)