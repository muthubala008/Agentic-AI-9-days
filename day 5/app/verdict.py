from collections.abc import Callable

from pydantic import BaseModel, Field, ValidationError, model_validator  # noqa: F401


class FailedRule(BaseModel):
    rule_id: int
    rule: str
    actual: str | float


class EligibilityVerdict(BaseModel):
    student_id: str = Field(pattern=r"^\d{2}[A-Z]{2}\d{3}$")
    drive_id: int
    eligible: bool
    failed_rules: list[FailedRule]
    summary: str = Field(min_length=1, max_length=280)

    @model_validator(mode="after")
    def validate_eligibility_consistency(self) -> "EligibilityVerdict":
        if self.eligible and len(self.failed_rules) > 0:
            raise ValueError(
                "eligible is True but failed_rules is non-empty, which contradicts eligibility"
            )
        if not self.eligible and len(self.failed_rules) == 0:
            raise ValueError(
                "eligible is False but failed_rules is empty, which contradicts eligibility"
            )
        return self


class VerdictInvalid(Exception):
    def __init__(self, attempts: int, last_errors: list):
        super().__init__(f"no valid verdict after {attempts} attempts")
        self.attempts = attempts
        self.last_errors = last_errors


Generate = Callable[[list[str]], str]


def _strip_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else ""
        t = t.rsplit("```", 1)[0]
    return t.strip()


def structured_verdict(generate: Generate, prompt: str, max_retries: int = 2) -> EligibilityVerdict:
    """Ask the model for an EligibilityVerdict; feed validation errors back; give up after max_retries."""
    messages = [prompt]
    last_errors = []

    for attempt in range(1, 1 + max_retries + 1):
        raw = generate(messages)
        clean = _strip_fences(raw)
        
        try:
            return EligibilityVerdict.model_validate_json(clean)
        except ValidationError as e:
            last_errors = e.errors()
            messages.append(raw)
            messages.append(
                f"JSON failed validation with errors: {last_errors}. Please fix the JSON and respond again."
            )

    raise VerdictInvalid(attempts=1 + max_retries, last_errors=last_errors)