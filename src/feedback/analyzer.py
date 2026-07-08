from src.feedback.models import Feedback
from src.tools.base import ToolResult


class FeedbackAnalyzer:
    def analyze(self, result: ToolResult) -> Feedback:
        if result.exit_code == 0:
            return Feedback(success=True)

        stderr_lower = result.stderr.lower()

        if "fail" in stderr_lower or "assertionerror" in stderr_lower or "assert" in stderr_lower:
            return Feedback(
                success=False,
                error_type="test_failure",
                detail=result.stderr[:500],
                summary="test failure detected",
            )

        if "timed out" in stderr_lower or "timeout" in stderr_lower:
            return Feedback(
                success=False,
                error_type="timeout",
                detail=result.stderr[:500],
                summary="command timed out",
            )

        return Feedback(
            success=False,
            error_type="command_error",
            detail=result.stderr[:500],
            summary=f"command failed with exit code {result.exit_code}",
        )