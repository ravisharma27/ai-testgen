import json

import pytest

from testgen.generator import GenerationError, generate_test_suite
from tests.conftest import FakeClient, valid_suite_dict

STORY = "As a user I want to reset my password."


def test_valid_first_try(valid_json):
    client = FakeClient([valid_json])
    result = generate_test_suite(STORY, client, model="gpt-5-mini")
    assert result.attempt_count == 1
    assert result.total_tokens == 100
    assert client.calls[0]["response_format"] == {"type": "json_object"}
    assert client.calls[0]["model"] == "gpt-5-mini"


def test_retries_after_invalid_json(valid_json):
    client = FakeClient(["Sure! Here are your tests: ...", valid_json])
    result = generate_test_suite(STORY, client, model="m")
    assert result.attempt_count == 2
    assert "not valid JSON" in result.attempts[0].error
    # The validator's complaint is fed back to the model on the retry
    assert "rejected by the validator" in client.calls[1]["messages"][-1]["content"]


def test_retries_after_schema_violation(valid_json):
    bad = valid_suite_dict()
    bad["test_cases"][0]["steps"] = []
    client = FakeClient([json.dumps(bad), valid_json])
    result = generate_test_suite(STORY, client, model="m")
    assert result.attempt_count == 2
    assert "test_cases.0.steps" in result.attempts[0].error


def test_gives_up_after_max_attempts():
    client = FakeClient(["nope", "still nope", "never"])
    with pytest.raises(GenerationError) as exc_info:
        generate_test_suite(STORY, client, model="m", max_attempts=3)
    assert len(exc_info.value.attempts) == 3
    assert len(client.calls) == 3


def test_empty_story_rejected():
    with pytest.raises(ValueError):
        generate_test_suite("   ", FakeClient([]), model="m")
