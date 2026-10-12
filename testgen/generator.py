"""Core loop: user story in, validated TestSuite out.

LLM output is treated like any untrusted input: parse it, validate it, and if it
fails, feed the exact validation errors back to the model and retry.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from pydantic import ValidationError

from . import prompts
from .schema import TestSuite

log = logging.getLogger(__name__)


class GenerationError(RuntimeError):
    """Raised when no valid output was produced within max_attempts."""

    def __init__(self, message: str, attempts: list[Attempt]):
        super().__init__(message)
        self.attempts = attempts


@dataclass
class Attempt:
    number: int
    raw_output: str
    error: str | None
    latency_s: float
    total_tokens: int | None


@dataclass
class GenerationResult:
    suite: TestSuite
    attempts: list[Attempt] = field(default_factory=list)

    @property
    def attempt_count(self) -> int:
        return len(self.attempts)

    @property
    def total_tokens(self) -> int:
        return sum(a.total_tokens or 0 for a in self.attempts)


def _format_validation_error(exc: ValidationError) -> str:
    lines = []
    for err in exc.errors():
        loc = ".".join(str(p) for p in err["loc"]) or "(root)"
        lines.append(f"- {loc}: {err['msg']}")
    return "\n".join(lines)


def _validate(raw: str) -> tuple[TestSuite | None, str | None]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, f"- Response is not valid JSON: {exc.msg} (line {exc.lineno})"
    try:
        return TestSuite.model_validate(data), None
    except ValidationError as exc:
        return None, _format_validation_error(exc)


def generate_test_suite(
    story: str,
    client: Any,
    model: str,
    max_attempts: int = 3,
) -> GenerationResult:
    """Generate and validate test cases for a user story.

    `client` is anything with an OpenAI-style `chat.completions.create`, which
    lets the unit tests pass in a fake client with no network calls.
    """
    if not story.strip():
        raise ValueError("story is empty")

    messages: list[dict[str, str]] = [
        {"role": "system", "content": prompts.system_prompt()},
        {"role": "user", "content": prompts.user_prompt(story)},
    ]
    attempts: list[Attempt] = []

    for number in range(1, max_attempts + 1):
        start = time.perf_counter()
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
        )
        latency = time.perf_counter() - start

        raw = response.choices[0].message.content or ""
        usage = getattr(response, "usage", None)
        tokens = getattr(usage, "total_tokens", None) if usage else None

        suite, error = _validate(raw)
        attempts.append(Attempt(number, raw, error, round(latency, 2), tokens))

        if suite is not None:
            log.info("valid output on attempt %d", number)
            return GenerationResult(suite=suite, attempts=attempts)

        log.warning("attempt %d rejected:\n%s", number, error)
        messages.append({"role": "assistant", "content": raw})
        messages.append({"role": "user", "content": prompts.retry_prompt(error)})

    raise GenerationError(
        f"no valid output after {max_attempts} attempts; last error:\n{attempts[-1].error}",
        attempts,
    )
