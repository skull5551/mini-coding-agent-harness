# Mini Coding Agent Harness

轻量级 Coding Agent 运行框架，管理 Agent 的任务执行流程，包括 LLM 调用、工具管理、状态控制、反馈循环和日志记录。

## 解决的问题

Coding Agent 虽然具备代码生成能力，但缺少可靠的工程控制机制：

- **行为不可预测**：Agent 可能无限循环、修改错误文件、选择错误工具
- **缺少反馈闭环**：生成代码后无法自动验证、测试、迭代修复
- **缺少执行记录**：决策过程、工具调用、错误原因不可追溯
- **难以测试验证**：Agent 行为依赖 LLM 输出，传统单元测试难以覆盖

Harness 通过 Agent Loop + Tool 管理 + Feedback 循环，提高 Coding Agent 的**可靠性**和**可观察性**。

## 目标用户

- **主要用户**：希望开发和维护 Coding Agent 的软件开发者
- **次要用户**：AI4SE 课程学习者或研究者，用于理解和实验 Agent 工作流程

## 架构

```
User → Web UI / CLI → Task Manager → Agent Loop (LLM + Tools + Feedback) → State (SQLite)
```

### 核心模块

| 模块 | 职责 |
|------|------|
| **Agent Loop** | 控制执行流程：DECIDE → ACT → OBSERVE 循环，管理最大步数限制 |
| **LLM Provider** | 统一 LLM 抽象接口，支持 Mock LLM 测试和 litellm 真实调用 |
| **Tool Executor** | 管理 Agent 可用的工具：读文件、写文件、执行命令、运行测试 |
| **Feedback Analyzer** | 分析工具执行结果，生成结构化反馈（test_failure / timeout / command_error） |
| **State Manager** | SQLite 持久化：Task / ExecutionStep / ToolCall / ApiKey |

## 快速开始

```bash
# 安装依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/

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
# 构建镜像
docker build -t mini-coding-agent .

# 运行容器
docker run -p 8000:8000 mini-coding-agent

# 或使用 docker compose
docker compose up -d
```

环境变量注入 API Key：

```bash
docker run -p 8000:8000 -e HARNESS_API_KEY_OPENAI=sk-xxx mini-coding-agent
```

## API Key 安全

- **不硬编码**：API Key 通过 Web UI 或 CLI 录入，不写在代码中
- **录入**：`POST /api/config/keys` 或 `agent-harness config set-key openai sk-xxx`
- **查看**：`GET /api/config/keys` 仅返回掩码格式（如 `sk-****abcd`），不返回完整 Key
- **删除**：`DELETE /api/config/keys/{provider}` 或通过 Web UI 删除
- **存储**：完整 Key 存储在 `key_value` 字段，API 接口只暴露 `key_masked` 字段

## 测试

```bash
pytest tests/
```

当前测试结果：**76/76 全部通过**

### 测试覆盖

| 测试文件 | 数量 | 覆盖内容 |
|----------|------|---------|
| `test_llm.py` | 5 | MockLLMProvider 预设响应、抽象接口 |
| `test_tools.py` | 11 | 文件读写、命令执行、路径遍历防护、ToolRegistry |
| `test_feedback.py` | 6 | FeedbackAnalyzer 成功/失败/超时分类 |
| `test_state.py` | 10 | SQLite CRUD、Task/Step/ToolCall/ApiKey |
| `test_task.py` | 8 | TaskManager 生命周期、workspace 管理 |
| `test_agent_loop.py` | 10 | Agent Loop 完整流程、超步数终止、错误恢复、反馈闭环 |
| `test_litellm_provider.py` | 8 | LiteLLMProvider Mock 测试 |
| `test_api.py` | 8 | FastAPI REST 端点集成测试 |
| `test_cli.py` | 6 | Typer CLI 命令测试 |
| `test_e2e.py` | 4 | 端到端：Agent Loop + API + 反馈闭环 |

### Mock LLM 测试

所有 Agent Loop 核心测试使用 `MockLLMProvider`，不依赖真实 LLM API：

- 预设响应序列，按顺序返回
- `call_history` 记录每次 LLM 调用收到的 messages，用于验证反馈注入
- 测试结果可重复、不依赖网络

## Demo 演示

一键运行 Harness 核心机制演示（不调用真实 LLM）：

```bash
python demo/agent_loop_demo.py
```

输出示例：

```
==================================================
  Coding Agent Harness — Mechanism Demo
==================================================

Task: 544b9a64-...
      fix add function bug

Step 1:
  LLM Decision: read_file
  Params:       {"path": "main.py"}
  Tool Result:  success

Step 2:
  LLM Decision: write_file
  Params:       {"path": "main.py", "content": "def add(a, b):\n    return a + b\n"}
  Tool Result:  success

Step 3:
  LLM Decision: run_test
  Params:       {"command": "pytest .../test_main.py"}
  Tool Result:  success

Step 4:
  LLM Decision: done
  Reason:       bug fixed

==================================================
  Final Result: SUCCESS
  Total Steps:  4
==================================================
```

## 技术栈

- Python 3.12 + FastAPI + Typer
- SQLite
- litellm (LLM 适配)
- Docker + pytest