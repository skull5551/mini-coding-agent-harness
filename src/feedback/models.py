from dataclasses import dataclass


@dataclass
class Feedback:
    success: bool
    error_type: str = ""
    detail: str = ""
    summary: str = ""