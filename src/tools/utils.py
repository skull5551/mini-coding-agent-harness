import os


def _is_safe_path(workspace: str, requested_path: str) -> bool:
    resolved = os.path.normpath(os.path.join(workspace, requested_path))
    return resolved.startswith(os.path.normpath(workspace))


def _resolve_path(workspace: str, requested_path: str) -> str:
    return os.path.normpath(os.path.join(workspace, requested_path))