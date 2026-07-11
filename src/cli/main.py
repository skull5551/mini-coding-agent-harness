import asyncio
import json
import typer
from src.agent.loop import AgentLoop
from src.feedback.analyzer import FeedbackAnalyzer
from src.llm.litellm_provider import LiteLLMProvider
from src.state.manager import StateManager
from src.task.manager import TaskManager
from src.tools.registry import ToolRegistry

app = typer.Typer()
config_app = typer.Typer()
app.add_typer(config_app, name="config")

_DB_OPTION = typer.Option("harness.db", "--db", help="SQLite database path")
_WS_OPTION = typer.Option("workspaces", "--workspace", help="Base workspace directory")


def _resolve(db: str, workspace: str) -> tuple[TaskManager, StateManager]:
    tm = TaskManager(db, base_workspace=workspace)
    return tm, tm.state


@app.command()
def run(
    description: str,
    db: str = _DB_OPTION,
    workspace: str = _WS_OPTION,
    model: str = typer.Option("gpt-4o", "--model", help="LLM model name"),
    provider: str = typer.Option("openai", "--provider", help="LLM provider name"),
):
    tm, sm = _resolve(db, workspace)
    task_id = tm.create_task(description)
    task = tm.get_task(task_id)

    api_key = sm.get_api_key(provider)
    if not api_key:
        typer.echo(f"Error: No API key configured for provider '{provider}'. Use 'config set-key' first.")
        raise typer.Exit(code=1)

    llm = LiteLLMProvider(model=model, api_key=api_key)
    tool_registry = ToolRegistry(workspace=task["workspace_path"])
    feedback_analyzer = FeedbackAnalyzer()
    loop = AgentLoop(
        llm=llm,
        tool_registry=tool_registry,
        feedback_analyzer=feedback_analyzer,
        task_mgr=tm,
    )

    result = asyncio.run(loop.run(task_id))
    typer.echo(json.dumps({
        "task_id": task_id,
        "status": result.status,
        "total_steps": result.total_steps,
        "final_message": result.final_message,
    }))


@app.command()
def status(
    task_id: str,
    db: str = _DB_OPTION,
    workspace: str = _WS_OPTION,
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
    db: str = _DB_OPTION,
    workspace: str = _WS_OPTION,
):
    tm, _ = _resolve(db, workspace)
    task = tm.get_task(task_id)
    if task is None:
        typer.echo(f"task not found: {task_id}", err=True)
        raise typer.Exit(code=1)
    steps = tm.get_steps(task_id)
    typer.echo(json.dumps(steps, default=str))


@config_app.command()
def set_key(
    provider: str,
    key: str = typer.Option(..., "--key", prompt=True, hide_input=True, help="API key (hidden input)"),
    db: str = _DB_OPTION,
    workspace: str = _WS_OPTION,
):
    _, sm = _resolve(db, workspace)
    sm.save_api_key(provider, key)
    typer.echo(json.dumps({"status": "ok"}))


@config_app.command(name="list-keys")
def list_keys(
    db: str = _DB_OPTION,
    workspace: str = _WS_OPTION,
):
    _, sm = _resolve(db, workspace)
    keys = sm.get_api_keys()
    typer.echo(json.dumps(keys, default=str))