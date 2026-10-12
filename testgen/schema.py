"""Pydantic models that define what a valid generated test case looks like.

The LLM is asked to return JSON matching these models. Anything that does not
validate is rejected and the model is asked to try again (see generator.py).
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


class Technique(str, Enum):
    """Test design techniques the generator is allowed to use."""

    HAPPY_PATH = "happy_path"
    BOUNDARY_VALUE = "boundary_value"
    EQUIVALENCE_PARTITIONING = "equivalence_partitioning"
    NEGATIVE = "negative"
    ERROR_GUESSING = "error_guessing"
    STATE_TRANSITION = "state_transition"
    DECISION_TABLE = "decision_table"


class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TestCase(BaseModel):
    """A single, executable-by-a-human test case."""

    __test__ = False  # stop pytest from trying to collect this class

    id: str = Field(pattern=r"^TC-\d{3}$", description="Sequential id, e.g. TC-001")
    title: str = Field(min_length=5, max_length=120)
    technique: Technique
    priority: Priority
    preconditions: list[str] = Field(default_factory=list)
    steps: list[str] = Field(min_length=1, max_length=15)
    expected_result: str = Field(min_length=3)
    test_data: dict[str, str] = Field(default_factory=dict)

    @field_validator("steps")
    @classmethod
    def steps_not_blank(cls, steps: list[str]) -> list[str]:
        if any(not s.strip() for s in steps):
            raise ValueError("steps must not contain blank entries")
        return steps


class TestSuite(BaseModel):
    """Everything the generator returns for one user story."""

    __test__ = False

    story_summary: str = Field(min_length=10)
    test_cases: list[TestCase] = Field(min_length=1, max_length=30)

    @model_validator(mode="after")
    def ids_are_unique(self) -> TestSuite:
        ids = [tc.id for tc in self.test_cases]
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        if dupes:
            raise ValueError(f"duplicate test case ids: {', '.join(dupes)}")
        return self

    def techniques_used(self) -> set[Technique]:
        return {tc.technique for tc in self.test_cases}
