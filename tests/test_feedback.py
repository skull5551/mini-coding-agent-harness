import pytest
from src.tools.base import ToolResult
from src.feedback.analyzer import FeedbackAnalyzer
from src.feedback.models import Feedback


def test_analyze_test_failure():
    result = ToolResult(stdout="", stderr="FAILED test_login", exit_code=1)
    feedback = FeedbackAnalyzer().analyze(result)
    assert not feedback.success
    assert feedback.error_type == "test_failure"


def test_analyze_success():
    result = ToolResult(stdout="all tests passed", stderr="", exit_code=0)
    feedback = FeedbackAnalyzer().analyze(result)
    assert feedback.success


def test_analyze_command_error():
    result = ToolResult(stdout="", stderr="command not found: foobar", exit_code=127)
    feedback = FeedbackAnalyzer().analyze(result)
    assert not feedback.success
    assert feedback.error_type == "command_error"


def test_analyze_timeout():
    result = ToolResult(stdout="", stderr="timed out", exit_code=124)
    feedback = FeedbackAnalyzer().analyze(result)
    assert not feedback.success
    assert feedback.error_type == "timeout"


def test_analyze_pytest_failure():
    result = ToolResult(
        stdout="",
        stderr="FAILURES\n____________________\ntest_calc.py::test_add - AssertionError: expected 5, got 4",
        exit_code=1,
    )
    feedback = FeedbackAnalyzer().analyze(result)
    assert not feedback.success
    assert "test_calc" in feedback.detail


def test_analyze_empty_result():
    result = ToolResult(stdout="", stderr="", exit_code=0)
    feedback = FeedbackAnalyzer().analyze(result)
    assert feedback.success
    assert feedback.error_type == ""