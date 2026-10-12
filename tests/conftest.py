import json
from types import SimpleNamespace

import pytest


def valid_suite_dict(n: int = 2) -> dict:
    return {
        "story_summary": "User resets a forgotten password via an emailed link.",
        "test_cases": [
            {
                "id": f"TC-{i:03d}",
                "title": f"Reset password scenario {i}",
                "technique": "boundary_value" if i % 2 else "happy_path",
                "priority": "high",
                "preconditions": ["User account exists"],
                "steps": ["Open login page", "Click 'Forgot password?'"],
                "expected_result": "Reset form is displayed",
                "test_data": {"email": "user@example.com"},
            }
            for i in range(1, n + 1)
        ],
    }


class FakeClient:
    """Mimics openai.OpenAI().chat.completions.create with scripted replies."""

    def __init__(self, replies: list[str]):
        self._replies = list(replies)
        self.calls: list[dict] = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        content = self._replies.pop(0)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
            usage=SimpleNamespace(total_tokens=100),
        )


@pytest.fixture
def valid_json() -> str:
    return json.dumps(valid_suite_dict())
