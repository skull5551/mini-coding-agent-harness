# Mini Coding Agent Harness

轻量级 Coding Agent 运行框架，管理 Agent 的任务执行流程，包括 LLM 调用、工具管理、状态控制、反馈循环和日志记录。

## 架构

```
User → Web UI / CLI → Task Manager → Agent Loop (LLM + Tools + Feedback) → State (SQLite)
```

## 快速开始

```bash
# 安装依赖
pip install -e ".[dev]"

# 启动 API 服务
uvicorn src.api.main:app --reload

# 或使用 CLI
agent-harness run "fix the login bug"
agent-harness status <task_id>
agent-harness logs <task_id>
```

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/tasks` | 创建任务 |
| GET | `/api/tasks` | 列出任务 |
| GET | `/api/tasks/{id}` | 查询任务 |
| GET | `/api/tasks/{id}/steps` | 查询步骤 |
| POST | `/api/config/keys` | 配置 API Key |
| GET | `/api/config/keys` | 列出 Keys |
| DELETE | `/api/config/keys/{provider}` | 删除 Key |

## Docker 部署

```bash
docker compose up -d
```

## 测试

```bash
pytest tests/
```

## 技术栈

- Python 3.12 + FastAPI + Typer
- SQLite + structlog
- litellm (LLM 适配)
- Docker + pytest