# Mini Coding Agent Harness — SPEC

## 1. 问题陈述

当前 Coding Agent 虽然具备代码生成能力，但缺少可靠的工程控制机制。主要问题包括：

- **行为不可预测**：Agent 可能无限循环、修改错误文件、或选择错误工具。
- **缺少反馈闭环**：Agent 生成代码后无法自动验证、测试、迭代修复。
- **缺少执行记录**：Agent 的决策过程、工具调用、错误原因不可追溯。
- **难以测试和验证**：Agent 行为依赖 LLM 输出，传统单元测试难以覆盖。

**核心问题**：如何通过工程机制（而非模型能力）提高 Coding Agent 的**可靠性**和**可观察性**？

本项目的答案是：**Coding Agent Harness** — 一个轻量级 Agent 运行框架，负责管理 Agent 的任务执行流程，包括 LLM 调用、工具管理、状态控制、反馈循环和日志记录。

## 2. 目标用户

### 主要用户：软件开发工程师
- 熟悉基本编程和 Git 工作流
- 能够阅读代码和测试结果
- 理解 LLM API 基本使用方式
- 希望在自己的项目中集成可靠的 Coding Agent

### 次要用户：AI4SE 课程学习者/研究者
- 用于理解和实验 Agent 工作流程
- 分析 Agent Loop、Feedback 循环等机制

### 非目标用户
- 无编程经验的普通用户
- 大规模 Benchmark 平台用户
- IDE 插件终端用户

## 3. 用户故事（INVEST）

以下用户故事符合 INVEST 原则（Independent, Negotiable, Valuable, Estimable, Small, Testable）。

### US-01：自动修复单文件 Bug

> 作为开发者，我希望让 Harness 自动定位并修复一个已知 Bug，以便减少手动调试时间。

**验收标准**：
- 用户提供项目代码路径、Bug 描述和测试命令
- Harness 创建任务并驱动 Agent 执行：分析 → 修改 → 测试 → 反馈循环
- 测试通过后返回最终修改和完整日志
- 测试失败时自动重试，不超过最大步数限制

### US-02：根据需求实现新功能

> 作为开发者，我希望让 Harness 根据功能需求描述在一个 Python 项目中实现新功能，以便加速功能开发。

**验收标准**：
- 用户提供功能描述和项目路径
- Agent 先分析项目结构，制定计划，编写测试，再实现功能
- Harness 记录所有修改文件和测试结果
- 新功能通过已有或新增的测试

### US-03：查看 Agent 执行日志

> 作为开发者，我希望在 Web UI 上查看 Agent 的完整执行日志，以便理解 Agent 为什么做出了某个决定。

**验收标准**：
- Web UI 展示 Agent 每一步的决策、工具调用和结果
- 日志结构化为可读格式（时间、动作、输入、输出）
- 支持按 Task ID 筛选和查看

### US-04：安全配置 API Key

> 作为开发者，我希望通过 Web UI 安全地配置和管理 LLM API Key，以便在不泄露密钥的前提下使用 Harness。

**验收标准**：
- API Key 通过 Web UI 表单录入，不显示明文
- 支持更新和删除已配置的 Key
- Key 存储在服务器端，不随请求明文传输
- 未配置 Key 时 Agent 无法调用真实 LLM

### US-05：使用 Mock LLM 验证 Agent 流程

> 作为开发者，我希望使用 Mock LLM 测试 Agent Loop 的核心机制，以便在不依赖真实 API 的情况下验证 Harness 的正确性。

**验收标准**：
- Mock LLM 返回预设的固定输出
- Agent Loop 在 Mock LLM 下完整执行：输入 → 分析 → 工具调用 → 反馈 → 结束
- 测试结果可重复、不依赖网络

### US-06：Agent 失败时人工接管

> 作为开发者，我希望当 Agent 多次尝试仍然失败时，Harness 能暂停任务并让我查看状态和日志，以便决定是继续还是终止。

**验收标准**：
- Harness 检测到连续失败次数超限后暂停任务
- Web UI 展示 Agent 思考过程摘要、已修改文件、错误日志
- 用户可选择提供额外信息、修改需求或终止任务

### US-07：通过 CLI 提交任务

> 作为开发者，我希望通过命令行提交 Agent 任务并查看状态，以便在终端工作流中集成 Harness。

**验收标准**：
- `agent-harness run "描述"` 创建并启动任务
- `agent-harness status TASK_ID` 查询任务状态
- `agent-harness logs TASK_ID` 查看任务日志

## 4. 功能规约

### F-01：Agent 执行循环（Agent Loop）
- 接收用户任务，驱动 Agent 执行完整流程
- 调用 LLM 获取决策，执行工具，获取反馈
- 支持最大步数限制，防止无限循环
- 支持成功/失败/暂停三种终止状态

### F-02：LLM 抽象层
- 定义统一 `chat(messages)` 接口
- 内置 `OpenAIProvider`、`ClaudeProvider`、`MockLLMProvider`
- 底层使用 `litellm` 适配多种模型
- Mock LLM 支持预设响应，用于测试

### F-03：工具系统
- `read_file(path)` — 读取文件内容
- `write_file(path, content)` — 写入/修改文件
- `execute_command(command)` — 执行 Shell 命令
- `run_test(command)` — 执行测试并收集结果
- 工具调用结果结构化返回（stdout, stderr, exit_code）

### F-04：反馈循环（Feedback Loop）
- 收集工具执行结果（测试输出、错误信息、退出码）
- 分析结果，判断任务是否成功
- 结构化为 Agent 可理解的反馈格式
- 将反馈送回 Agent Loop 驱动下一步

### F-05：状态管理
- 使用 SQLite 持久化存储
- Task 表：id, description, status, created_at, updated_at
- Step 表：task_id, step_number, action, input, output, timestamp
- ToolCall 表：task_id, tool_name, input, output, status

### F-06：任务管理
- 创建任务、查询状态、更新生命周期
- 支持任务取消和暂停

### F-07：结构化日志
- 使用 structlog 记录所有 Agent 行为
- 日志包含：事件类型、task_id、动作、输入输出摘要
- 保存到 SQLite 和 JSON 日志文件

### F-08：Web UI
- 创建任务页面
- 任务状态页面（实时更新）
- Agent 执行日志查看页面
- API Key 管理页面

### F-09：CLI
- `agent-harness run <description>`
- `agent-harness status <task_id>`
- `agent-harness logs <task_id>`
- `agent-harness config set-key <provider>`

### F-10：安全配置
- API Key 通过 Web UI/CLI 录入
- 服务端加密存储（环境变量或加密文件）
- 不显示明文，不随请求传输
- 支持更新和删除

## 5. 非功能需求

| 需求 | 说明 |
|------|------|
| 可靠性 | Agent Loop 在最大步数内必须终止，无无限循环 |
| 可观察性 | 所有 Agent 决策和工具调用均可追溯 |
| 可测试性 | 使用 Mock LLM 可完整测试 Agent Loop 核心流程 |
| 可扩展性 | 新增 LLM Provider 或 Tool 无需修改 Agent Loop |
| 安全性 | API Key 不硬编码、不泄露、不随请求传输 |
| 可重复性 | Mock LLM 测试结果确定且可重复 |
| 隔离性 | 每个 Task 在独立 workspace 中执行 |

## 6. 安全设计

### 6.1 威胁模型

| 威胁 | 描述 | 严重等级 |
|------|------|---------|
| T1 | API Key 硬编码在代码中，提交到 Git | 高 |
| T2 | API Key 在日志或 Web UI 中明文显示 | 高 |
| T3 | Agent 执行恶意命令，破坏宿主机环境 | 中 |
| T4 | Agent 读取或修改未授权文件 | 中 |
| T5 | LLM API Key 通过网络被截获 | 中 |

### 6.2 API Key 存储方案

- Key 不写在代码中，不写在配置文件中提交到 Git
- 服务启动时通过环境变量 `HARNESS_API_KEY_OPENAI` / `HARNESS_API_KEY_ANTHROPIC` 注入
- 或通过 Web UI 表单录入，存储到服务端内存/加密文件
- Web UI 展示时仅显示 `sk-****...****` 格式的掩码
- API 接口不返回 Key 明文

### 6.3 执行安全

- 每个 Task 在独立临时 workspace 中执行
- 默认禁止访问 workspace 之外的路径
- 命令执行限制在 workspace 内
- 提供命令白名单机制（可选）

## 7. 系统架构

```
┌──────────────────────────────────────────────────┐
│                    Web UI                         │
│         (FastAPI + React/Vue)                     │
└────────────────────┬─────────────────────────────┘
                     │ REST API
┌────────────────────▼─────────────────────────────┐
│               Task Manager                        │
│            (FastAPI Router)                       │
└────────────────────┬─────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────┐
│              Agent Loop (Core)                    │
│                                                   │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ LLM Prov.│  │ Tool Exec│  │ Feedback Anal.│  │
│  │ (absract)│  │ (asyncio)│  │ (result parse)│  │
│  └────┬─────┘  └────┬─────┘  └───────┬───────┘  │
│       │             │                │           │
│  ┌────▼─────┐  ┌────▼─────┐  ┌───────▼───────┐  │
│  │ litellm  │  │ workspace│  │ State Manager │  │
│  │ Mock LLM │  │ sandbox  │  │ (SQLite)      │  │
│  └──────────┘  └──────────┘  └───────────────┘  │
└──────────────────────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────┐
│               Logger (structlog)                  │
│         → SQLite / JSON Log Files                │
└──────────────────────────────────────────────────┘
```

## 8. 数据流

```
用户提交任务
    │
    ▼
Task Manager 创建 Task (状态: pending)
    │
    ▼
Agent Loop 启动
    │
    ▼
Loop: 调用 LLM Provider → 获取决策
    │
    ▼
决策 = 工具调用? ──是──→ Tool Executor 执行
    │                        │
   否                        ▼
    │                 收集执行结果
    ▼                        │
决策 = 完成? ──是──→ 任务完成   │
    │                        │
   否                        ▼
    │                 Feedback Analyzer 分析
    ▼                        │
返回反馈给 LLM ──────────────┘
    │
    ▼
Logger 记录每一步
    │
    ▼
Web UI 实时展示状态
```

## 9. 数据模型

### Task
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| description | TEXT | 任务描述 |
| status | TEXT | pending/running/success/failed/paused |
| max_steps | INT | 最大执行步数 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |
| workspace_path | TEXT | 工作目录路径 |

### ExecutionStep
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| task_id | UUID | 外键 → Task |
| step_number | INT | 步骤序号 |
| action | TEXT | Agent 决策动作 |
| input_summary | TEXT | 决策输入摘要 |
| output_summary | TEXT | 执行结果摘要 |
| timestamp | DATETIME | 时间戳 |

### ToolCall
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| task_id | UUID | 外键 → Task |
| step_id | UUID | 外键 → ExecutionStep |
| tool_name | TEXT | 工具名 |
| input | TEXT | 工具输入 |
| output | TEXT | 工具输出 |
| exit_code | INT | 退出码 |
| status | TEXT | success/failed |

### ApiKey
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| provider | TEXT | openai/anthropic/... |
| key_masked | TEXT | 掩码后的 Key |
| created_at | DATETIME | 创建时间 |

## 10. 技术选型与理由

| 模块 | 选型 | 理由 |
|------|------|------|
| 语言 | Python 3.12 | 课程要求，生态成熟 |
| 后端框架 | FastAPI | 异步支持好，适合 Agent 任务调度 |
| LLM 底层 | litellm | 统一接口，支持多种模型 |
| 数据库 | SQLite | 轻量，无需额外服务，适合 MVP |
| 日志 | structlog | 结构化日志，便于分析和展示 |
| CLI | Typer | 类型提示驱动，开发体验好 |
| 测试 | pytest | 标准 Python 测试框架 |
| 前端 | React/Vue | 前后端分离，满足课程 Web UI 要求 |
| 部署 | Docker | 环境一致性，便于分发 |
| 工具执行 | asyncio subprocess | 异步非阻塞，适合 Web 服务 |

## 11. 分发方案

### Docker 镜像
- 基于 `python:3.12-slim`
- 包含 Harness 核心 + Web UI + CLI
- 单容器部署
- 通过环境变量注入 API Key

### 使用方式
1. `docker run -p 8000:8000 mini-coding-agent`
2. 打开浏览器访问 `http://localhost:8000`
3. 在 Web UI 中配置 API Key 并提交任务

## 12. 验收标准

| # | 验收项 | 验证方式 |
|---|--------|---------|
| A1 | Agent Loop 可在 Mock LLM 下完整执行 | pytest 端到端测试 |
| A2 | Tool Executor 可读写文件、执行命令 | pytest 单元测试 |
| A3 | Feedback Analyzer 正确分析测试结果 | pytest 单元测试 |
| A4 | 状态管理使用 SQLite 持久化 | pytest 集成测试 |
| A5 | Web UI 可创建任务、查看状态和日志 | 手动测试 |
| A6 | CLI 可创建任务、查询状态 | pytest + 手动 |
| A7 | API Key 安全录入，不显示明文 | 手动测试 |
| A8 | Mock LLM 测试结果可重复 | pytest 三次运行结果一致 |
| A9 | Docker 镜像可正常启动和使用 | 手动测试 |
| A10 | 所有模块均有 pytest 测试覆盖 | pytest --cov |

## 13. 风险与未决问题

### 已识别风险
见风险分析章节（第 7 步 brainstorming 结果），包括：范围失控、核心机制不够突出、Agent 行为不可预测、Mock LLM 测试、环境隔离、SPEC 清晰度、交付完整性。

### 未决问题
- Q1: Web UI 前端框架的具体选择（React vs Vue），待确认团队熟悉度后决定
- Q2: Tool 权限控制策略的颗粒度（文件级 vs 目录级），MVP 先用目录级
- Q3: 是否支持流式输出 Agent 决策过程到 Web UI，视时间决定

---

## 附录 A：Harness 领域设计

### 核心实体

```
Agent: 由 LLM 驱动的代码修改智能体，通过 Harness 控制执行
Harness: 控制 Agent 执行流程的框架层
Task: 用户提交的单一任务单元
Tool: Agent 可调用的外部操作（读文件、写文件、执行命令、运行测试）
Feedback: 工具执行结果的结构化分析
Workspace: Task 执行的隔离工作目录
```

### 领域关系

```
User ──提交──→ Task
Task ──驱动──→ Agent
Agent ──使用──→ Harness
Harness ──管理──→ Tool
Harness ──生成──→ Feedback
Task ──拥有──→ Workspace
```

## 附录 B：Agent Loop 机制设计

```
状态: IDLE → RUNNING → (DECIDE → ACT → OBSERVE)ⁿ → SUCCESS/FAILED/PAUSED

IDLE: 等待任务
RUNNING: 任务执行中
DECIDE: 调用 LLM 获取下一动作决策
ACT: 执行决策指定的工具调用
OBSERVE: 收集并分析执行结果
SUCCESS: 任务完成（测试通过 / Agent 主动完成）
FAILED: 超出最大步数 / Agent 主动放弃
PAUSED: 等待人工介入
```

最大步数 N 默认为 20，可通过 Task 配置。

## 附录 C：Tool 调用机制

```
Agent Decision (from LLM):
  {
    "tool": "read_file",
    "params": {"path": "src/main.py"}
  }

Tool Executor:
  1. 校验工具名是否在注册表中
  2. 校验参数格式
  3. 在 Workspace 内执行操作
  4. 返回结构化结果

Tool 注册:
  registry = {
    "read_file": ReadFileTool(),
    "write_file": WriteFileTool(),
    "execute_command": ExecuteCommandTool(),
    "run_test": RunTestTool(),
  }
```

## 附录 D：Feedback 循环机制

```
执行结果 (原始)
  │
  ▼
Feedback Analyzer:
  1. 解析 exit_code
  2. 提取错误信息
  3. 判断测试通过/失败
  4. 提取关键信息（错误行、失败测试名）
  │
  ▼
结构化反馈 (给 Agent):
  {
    "success": false,
    "error_type": "test_failure",
    "detail": "AssertionError in test_login: expected True, got False",
    "stdout": "...",
    "stderr": "..."
  }
  │
  ▼
Agent Loop 将反馈注入 LLM 的下一轮调用
```

## 附录 E：Mock LLM 测试策略

### Mock LLM 设计

```python
class MockLLMProvider:
    def __init__(self, responses: list[dict]):
        # responses: 预设的响应序列
        # 每次调用返回下一个响应
        self.responses = responses
        self.call_count = 0

    def chat(self, messages):
        response = self.responses[self.call_count]
        self.call_count += 1
        return response
```

### 测试场景

| 测试 | Mock 响应序列 | 预期行为 |
|------|--------------|---------|
| 单步修复 | [read_file → write_file → done] | Agent 完成修复 |
| 多轮反馈 | [read → write → test_fails → read → write → done] | Agent 根据反馈重试 |
| 达到上限 | [write → test → write → test → ... × 20] | Agent 在 20 步后终止 |
| 无效工具 | [exec("rm -rf /")] | Harness 拒绝执行 |

### 测试原则

1. 所有 Agent Loop 核心测试使用 Mock LLM
2. 真实 LLM 仅用于最终演示
3. Mock 测试结果必须可重复
4. 每个测试覆盖一个明确的 Agent 行为场景