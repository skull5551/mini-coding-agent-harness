import os
import pytest
from src.task.manager import TaskManager


def test_task_lifecycle(tmp_path):
    db_path = tmp_path / "test.db"
    mgr = TaskManager(str(db_path))
    task_id = mgr.create_task("fix bug")
    task = mgr.get_task(task_id)
    assert task["status"] == "pending"
    mgr.start_task(task_id)
    task = mgr.get_task(task_id)
    assert task["status"] == "running"


def test_create_task_creates_workspace(tmp_path):
    db_path = tmp_path / "test.db"
    mgr = TaskManager(str(db_path), base_workspace=str(tmp_path / "workspaces"))
    task_id = mgr.create_task("test")
    task = mgr.get_task(task_id)
    assert task["workspace_path"] is not None
    assert os.path.isdir(task["workspace_path"])


def test_complete_task(tmp_path):
    db_path = tmp_path / "test.db"
    mgr = TaskManager(str(db_path))
    task_id = mgr.create_task("test")
    mgr.start_task(task_id)
    mgr.complete_task(task_id)
    task = mgr.get_task(task_id)
    assert task["status"] == "success"


def test_fail_task(tmp_path):
    db_path = tmp_path / "test.db"
    mgr = TaskManager(str(db_path))
    task_id = mgr.create_task("test")
    mgr.start_task(task_id)
    mgr.fail_task(task_id)
    task = mgr.get_task(task_id)
    assert task["status"] == "failed"


def test_pause_task(tmp_path):
    db_path = tmp_path / "test.db"
    mgr = TaskManager(str(db_path))
    task_id = mgr.create_task("test")
    mgr.start_task(task_id)
    mgr.pause_task(task_id)
    task = mgr.get_task(task_id)
    assert task["status"] == "paused"


def test_get_nonexistent_task(tmp_path):
    db_path = tmp_path / "test.db"
    mgr = TaskManager(str(db_path))
    task = mgr.get_task("nonexistent")
    assert task is None


def test_list_tasks(tmp_path):
    db_path = tmp_path / "test.db"
    mgr = TaskManager(str(db_path))
    t1 = mgr.create_task("task 1")
    t2 = mgr.create_task("task 2")
    tasks = mgr.list_tasks()
    assert len(tasks) == 2


def test_mark_step(tmp_path):
    db_path = tmp_path / "test.db"
    mgr = TaskManager(str(db_path))
    task_id = mgr.create_task("test")
    mgr.start_task(task_id)
    mgr.mark_step(task_id, action="read_file", input_summary="read main.py")
    mgr.mark_step(task_id, action="write_file", input_summary="write fix")
    steps = mgr.get_steps(task_id)
    assert len(steps) == 2
    assert steps[0]["action"] == "read_file"
    assert steps[1]["action"] == "write_file"