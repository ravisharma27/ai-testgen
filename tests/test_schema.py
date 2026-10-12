import pytest
from pydantic import ValidationError

from testgen.schema import Technique, TestSuite
from tests.conftest import valid_suite_dict


def test_valid_suite_parses():
    suite = TestSuite.model_validate(valid_suite_dict(3))
    assert len(suite.test_cases) == 3
    assert suite.techniques_used() == {Technique.BOUNDARY_VALUE, Technique.HAPPY_PATH}


def test_unknown_technique_rejected():
    data = valid_suite_dict()
    data["test_cases"][0]["technique"] = "vibes_based"
    with pytest.raises(ValidationError, match="technique"):
        TestSuite.model_validate(data)


@pytest.mark.parametrize("bad_id", ["TC-1", "tc-001", "TC-0001", "001"])
def test_id_format_enforced(bad_id):
    data = valid_suite_dict()
    data["test_cases"][0]["id"] = bad_id
    with pytest.raises(ValidationError):
        TestSuite.model_validate(data)


def test_empty_steps_rejected():
    data = valid_suite_dict()
    data["test_cases"][0]["steps"] = []
    with pytest.raises(ValidationError):
        TestSuite.model_validate(data)


def test_blank_step_rejected():
    data = valid_suite_dict()
    data["test_cases"][0]["steps"] = ["Open page", "   "]
    with pytest.raises(ValidationError, match="blank"):
        TestSuite.model_validate(data)


def test_duplicate_ids_rejected():
    data = valid_suite_dict(2)
    data["test_cases"][1]["id"] = "TC-001"
    with pytest.raises(ValidationError, match="duplicate"):
        TestSuite.model_validate(data)


def test_empty_suite_rejected():
    data = valid_suite_dict()
    data["test_cases"] = []
    with pytest.raises(ValidationError):
        TestSuite.model_validate(data)
