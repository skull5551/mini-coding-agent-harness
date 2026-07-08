from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import tasks, config
from src.state.manager import StateManager
from src.task.manager import TaskManager


def create_app(db_path: str = "harness.db", base_workspace: str = "workspaces") -> FastAPI:
    state_mgr = StateManager(db_path)
    task_mgr = TaskManager(db_path, base_workspace=base_workspace)

    tasks.init(task_mgr)
    config.init(state_mgr)

    app = FastAPI(title="Mini Coding Agent Harness")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(tasks.router)
    app.include_router(config.router)

    return app