from src.feedback.models import Feedback
from src.tools.base import ToolResult


class FeedbackAnalyzer:
    def analyze(self, result: ToolResult) -> Feedback:
        if result.exit_code == 0:
            return Feedback(success=True)

        combined = (result.stderr + " " + result.stdout).lower()
        detail_source = result.stderr + result.stdout
        detail = detail_source[-500:] if len(detail_source) > 500 else detail_source[:500]

        if "fail" in combined or "assertionerror" in combined:
            return Feedback(
                success=False,
                error_type="test_failure",
                detail=detail,
                summary="test failure detected",
            )

        if "timed out" in combined or "timeout" in combined:
            return Feedback(
                success=False,
                error_type="timeout",
                detail=detail,
                summary="command timed out",
            )

        return Feedback(
            success=False,
            error_type="command_error",
            detail=detail,
            summary=f"command failed with exit code {result.exit_code}",
        )