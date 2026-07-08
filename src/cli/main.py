import json
import typer
from src.task.manager import TaskManager
from src.state.manager import StateManager

app = typer.Typer()
config_app = typer.Typer()
app.add_typer(config_app, name="config")


def _resolve(db: str, workspace: str) -> tuple[TaskManager, StateManager]:
    tm = TaskManager(db, base_workspace=workspace)
    sm = StateManager(db)
    return tm, sm


@app.callback()
def main(
    db: str = typer.Option("harness.db", "--db", help="SQLite database path"),
    workspace: str = typer.Option("workspaces", "--workspace", help="Base workspace directory"),
):
    pass


@app.command()
def run(
    description: str,
    db: str = typer.Option("harness.db", "--db", hidden=True),
    workspace: str = typer.Option("workspaces", "--workspace", hidden=True),
):
    tm, _ = _resolve(db, workspace)
    task_id = tm.create_task(description)
    task = tm.get_task(task_id)
    typer.echo(json.dumps({"task_id": task_id, "status": task["status"]}))


@app.command()
def status(
    task_id: str,
    db: str = typer.Option("harness.db", "--db", hidden=True),
    workspace: str = typer.Option("workspaces", "--workspace", hidden=True),
):
    tm, _ = _resolve(db, workspace)
    task = tm.get_task(task_id)
    if task is None:
        typer.echo(f"task not found: {task_id}", err=True)
        raise typer.Exit(code=1)
    typer.echo(json.dumps(task, default=str))


@app.command()
def logs(
    task_id: str,
    db: str = typer.Option("harness.db", "--db", hidden=True),
    workspace: str = typer.Option("workspaces", "--workspace", hidden=True),
):
    tm, _ = _resolve(db, workspace)
    steps = tm.get_steps(task_id)
    typer.echo(json.dumps(steps, default=str))


@config_app.command()
def set_key(
    provider: str,
    key: str,
    db: str = typer.Option("harness.db", "--db", hidden=True),
    workspace: str = typer.Option("workspaces", "--workspace", hidden=True),
):
    _, sm = _resolve(db, workspace)
    sm.save_api_key(provider, key)
    typer.echo(json.dumps({"status": "ok"}))


@config_app.command(name="list-keys")
def list_keys(
    db: str = typer.Option("harness.db", "--db", hidden=True),
    workspace: str = typer.Option("workspaces", "--workspace", hidden=True),
):
    _, sm = _resolve(db, workspace)
    keys = sm.get_api_keys()
    typer.echo(json.dumps(keys, default=str))