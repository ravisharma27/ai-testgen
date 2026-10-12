"""Prompt templates. Kept in one place so prompt changes are easy to review and diff."""

import json

from .schema import TestSuite

SYSTEM_PROMPT = """You are a senior QA engineer who designs rigorous, non-redundant test cases.

Rules:
- Derive tests only from the user story and its acceptance criteria. Do not invent features.
- Cover every acceptance criterion with at least one test.
- Apply boundary value analysis to every numeric or length limit (min-1, min, max, max+1).
- Include negative tests for invalid input and error handling.
- Steps are short imperative actions a tester can follow. One action per step.
- expected_result is specific and observable (a message, a state, a value), never "works correctly".
- Number ids sequentially: TC-001, TC-002, ...

Respond with a single JSON object only, no markdown, matching this JSON schema:
{schema}
"""

USER_PROMPT = """User story:
\"\"\"
{story}
\"\"\"
"""

RETRY_PROMPT = """Your previous response was rejected by the validator:

{errors}

Return the full corrected JSON object only."""


def system_prompt() -> str:
    schema = json.dumps(TestSuite.model_json_schema(), indent=2)
    return SYSTEM_PROMPT.format(schema=schema)


def user_prompt(story: str) -> str:
    return USER_PROMPT.format(story=story.strip())


def retry_prompt(errors: str) -> str:
    return RETRY_PROMPT.format(errors=errors)
