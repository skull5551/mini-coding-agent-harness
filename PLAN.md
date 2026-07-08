# Mini Coding Agent Harness — PLAN

## 任务拆分说明

本文档按照 subagent-driven-development 要求拆分实现任务。

- **并行标记** `[PARALLEL]`：可以与同级任务同时执行
- **顺序标记** `[SEQUENTIAL]`：必须在前置任务完成后执行
- 每个任务首先编写**失败测试**（TDD 模式）

---

## Phase 0：项目基础设施

### Task 0.1：项目结构初始化 `[PARALLEL]`

- **目标**：创建 Python 项目骨架，配置包管理和基础工具
- **涉及文件**：
  - `pyproject.toml`
  - `.gitignore`
  - `src/__init__.py`
  - `tests/__init__.py`
  - `Dockerfile`（骨架）
- **实现要点**：
  - 使用 `pyproject.toml` 管理依赖
  - 配置 `[project.scripts]` 入口点为 CLI
  - 配置 `[tool.pytest.ini_options]`
- **依赖关系**：无
- **验证步骤**：
  - `pip install -e .` 可正常安装
  - `pytest` 可发现测试（初始无测试）
- **首先编写的测试**：无（基础设施无业务逻辑）

### Task 0.2：项目文档初始化 `[PARALLEL]`

- **目标**：创建 README.md、AGENT_LOG.md、REFLECTION.md 骨架
- **涉及文件**：
  - `README.md`
  - `AGENT_LOG.md`
  - `REFLECTION.md`
- **实现要点**：
  - README.md 包含项目简介、快速开始、架构图
  - AGENT_LOG.md 记录每步 Agent 协作过程
  - REFLECTION.md 课程反思
- **依赖关系**：无
- **验证步骤**：文档内容完整可读
- **首先编写的测试**：无

### Task 0.3：CI 配置 `[PARALLEL]`

- **目标**：配置 GitHub Actions 或等效 CI
- **涉及文件**：
  - `.github/workflows/ci.yml`
- **实现要点**：
  - 每次 push 自动运行 pytest
  - 使用 Python 3.12
- **依赖关系**：无
- **验证步骤**：CI 在 push 后自动运行
- **首先编写的测试**：无

---

## Phase 1：核心抽象层（可并行）

### Task 1.1：LLM Provider 抽象接口 + Mock LLM `[PARALLEL]`

- **目标**：定义 LLM 统一接口，实现 Mock LLM Provider
- **涉及文件**：
  - `src/llm/__init__.py`
  - `src/llm/base.py` — 抽象基类 `LLMProvider`
  - `src/llm/mock.py` — `MockLLMProvider`
- **实现要点**：
  - `LLMProvider` 定义 `chat(messages: list) -> str`
  - `MockLLMProvider` 接受预设响应列表，每次调用返回下一个
  - 支持响应耗尽时抛出明确异常
- **依赖关系**：Task 0.1
- **验证步骤**：
  - MockLLMProvider 按顺序返回预设响应
  - 超过预设响应数时抛出异常
- **首先编写的测试**：
  ```python
  def test_mock_llm_returns_preset_responses():
      provider = MockLLMProvider(responses=["tool: read_file", "tool: write_file"])
      assert provider.chat([]) == "tool: read_file"
      assert provider.chat([]) == "tool: write_file"

  def test_mock_llm_exhausted_raises():
      provider = MockLLMProvider(responses=["only one"])
      provider.chat([])
      with pytest.raises(StopIteration):
          provider.chat([])
  ```

### Task 1.2：Tool 系统抽象接口 + 基础工具实现 `[PARALLEL]`

- **目标**：定义 Tool 接口，实现文件读写、命令执行、测试执行工具
- **涉及文件**：
  - `src/tools/__init__.py`
  - `src/tools/base.py` — `BaseTool`
  - `src/tools/registry.py` — `ToolRegistry`
  - `src/tools/read_file.py` — `ReadFileTool`
  - `src/tools/write_file.py` — `WriteFileTool`
  - `src/tools/execute_command.py` — `ExecuteCommandTool`
  - `src/tools/run_test.py` — `RunTestTool`
- **实现要点**：
  - `BaseTool` 定义 `execute(params) -> ToolResult`
  - `ToolResult` 包含：stdout, stderr, exit_code, success
  - `ToolRegistry` 管理工具注册和查找
  - 文件操作限制在 workspace 路径内
  - 命令执行使用 asyncio 异步
- **依赖关系**：Task 0.1
- **验证步骤**：
  - 读写文件工具在 workspace 内正常工作
  - 命令执行工具返回 stdout/stderr/exit_code
  - 路径遍历攻击被拒绝
- **首先编写的测试**：
  ```python
  async def test_read_write_file(tmp_path):
      tool = ReadFileTool(workspace=tmp_path)
      write = WriteFileTool(workspace=tmp_path)
      await write.execute({"path": "test.txt", "content": "hello"})
      result = await tool.execute({"path": "test.txt"})
      assert result.stdout == "hello"

  async def test_path_traversal_rejected(tmp_path):
      tool = ReadFileTool(workspace=tmp_path)
      result = await tool.execute({"path": "../etc/passwd"})
      assert not result.success
  ```

### Task 1.3：Feedback Analyzer `[PARALLEL]`

- **目标**：实现反馈分析模块，将原始执行结果转为结构化反馈
- **涉及文件**：
  - `src/feedback/__init__.py`
  - `src/feedback/analyzer.py` — `FeedbackAnalyzer`
  - `src/feedback/models.py` — `Feedback`
- **实现要点**：
  - `analyze(result: ToolResult) -> Feedback`
  - Feedback 包含：success, error_type, detail, summary
  - 支持测试失败、命令错误、超时等错误类型
- **依赖关系**：Task 1.2
- **验证步骤**：
  - 测试失败 -> Feedback.error_type == "test_failure"
  - 命令成功 -> Feedback.success == True
- **首先编写的测试**：
  ```python
  def test_analyze_test_failure():
      result = ToolResult(stdout="", stderr="FAILED test_login", exit_code=1)
      feedback = FeedbackAnalyzer().analyze(result)
      assert not feedback.success
      assert feedback.error_type == "test_failure"

  def test_analyze_success():
      result = ToolResult(stdout="all tests passed", stderr="", exit_code=0)
      feedback = FeedbackAnalyzer().analyze(result)
      assert feedback.success
  ```

---

## Phase 2：状态与任务管理（可并行）

### Task 2.1：SQLite 状态管理 `[PARALLEL]`

- **目标**：实现基于 SQLite 的状态持久化管理
- **涉及文件**：
  - `src/state/__init__.py`
  - `src/state/database.py` — 数据库初始化 + 连接管理
  - `src/state/models.py` — 数据模型定义
  - `src/state/manager.py` — `StateManager`
- **实现要点**：
  - 使用 `sqlite3` 标准库
  - 自动建表（Task, ExecutionStep, ToolCall, ApiKey）
  - CRUD 操作封装
- **依赖关系**：Task 0.1
- **验证步骤**：
  - 创建 Task 后可在 DB 中查到
  - 添加 Step 后关联查询正确
- **首先编写的测试**：
  ```python
  def test_create_and_query_task(tmp_path):
      db_path = tmp_path / "test.db"
      mgr = StateManager(db_path)
      task_id = mgr.create_task("fix login bug")
      task = mgr.get_task(task_id)
      assert task.description == "fix login bug"
      assert task.status == "pending"
  ```

### Task 2.2：Task Manager `[PARALLEL]`

- **目标**：实现任务管理模块，作为 Agent Loop 的入口
- **涉及文件**：
  - `src/task/__init__.py`
  - `src/task/manager.py` — `TaskManager`
- **实现要点**：
  - 创建任务 → 分配 workspace → 启动 Agent Loop
  - 查询任务状态和步骤
  - 支持暂停 / 取消任务
- **依赖关系**：Task 2.1
- **验证步骤**：
  - 创建任务后状态为 pending
  - 启动后状态为 running
- **首先编写的测试**：
  ```python
  def test_task_lifecycle(tmp_path):
      db_path = tmp_path / "test.db"
      mgr = TaskManager(db_path)
      task_id = mgr.create_task("fix bug")
      assert mgr.get_task(task_id).status == "pending"
      mgr.start(task_id)
      assert mgr.get_task(task_id).status == "running"
  ```

---

## Phase 3：Agent Loop 核心（必须顺序）

### Task 3.1：Agent Loop 基础实现 `[SEQUENTIAL]`

- **前置任务**：Task 1.1, Task 1.2, Task 1.3, Task 2.2
- **目标**：实现 Agent 执行循环核心
- **涉及文件**：
  - `src/agent/__init__.py`
  - `src/agent/loop.py` — `AgentLoop`
  - `src/agent/models.py` — `AgentState`, `AgentDecision`
- **实现要点**：
  - 状态机：IDLE → RUNNING → (DECIDE → ACT → OBSERVE)ⁿ → 终止
  - DECIDE：调用 LLM Provider 获取决策
  - ACT：从 LLM 响应解析工具调用 → 通过 ToolRegistry 执行
  - OBSERVE：通过 FeedbackAnalyzer 分析结果
  - 终止条件：Agent 主动完成 / 测试通过 / 超过最大步数
  - 最大步数限制，防止无限循环
- **依赖关系**：[Task 1.1, Task 1.2, Task 1.3, Task 2.2] → Task 3.1
- **验证步骤**：
  - Mock LLM 下完整执行：任务输入 → 分析 → 工具调用 → 反馈 → 完成
  - 超过最大步数时自动终止
- **首先编写的测试**：
  ```python
  async def test_agent_loop_complete_flow(tmp_path, mock_llm_responses):
      db_path = tmp_path / "test.db"
      state_mgr = StateManager(db_path)
      task_mgr = TaskManager(state_mgr)
      loop = AgentLoop(llm=MockLLMProvider(responses=mock_llm_responses),
                       tool_registry=ToolRegistry(workspace=tmp_path),
                       feedback_analyzer=FeedbackAnalyzer(),
                       task_mgr=task_mgr)
      task_id = task_mgr.create_task("fix bug")
      result = await loop.run(task_id)
      assert result.status in ("success", "failed")

  async def test_agent_loop_max_steps(tmp_path):
      # Mock LLM 始终返回一个不会完成的动作
      responses = [{"tool": "read_file", "params": {"path": "test.py"}}] * 25
      loop = AgentLoop(llm=MockLLMProvider(responses=responses), ...)
      task_id = task_mgr.create_task("test")
      result = await loop.run(task_id, max_steps=20)
      assert result.status == "failed"
      assert result.steps == 20
  ```

### Task 3.2：真实 LLM Provider（litellm 适配） `[PARALLEL]`

- **目标**：实现基于 litellm 的真实 LLM Provider
- **涉及文件**：
  - `src/llm/litellm_provider.py` — `LiteLLMProvider`
  - `src/llm/openai_provider.py` — `OpenAIProvider`（可选）
- **实现要点**：
  - 通过 litellm 调用 OpenAI / Anthropic / Gemini
  - 支持 model 参数配置
  - 错误处理和重试逻辑
- **依赖关系**：Task 1.1
- **验证步骤**：
  - 配置有效 API Key 后可正常调用
  - 无效 Key 时抛出明确错误
- **首先编写的测试**（需要 Mock API）：
  ```python
  @pytest.mark.asyncio
  async def test_litellm_provider_with_mock():
      # 使用 responses 库 mock HTTP 调用
      pass  # 视时间决定是否编写
  ```

---

## Phase 4：Web UI + CLI（可并行）

### Task 4.1：FastAPI 后端 + REST API `[PARALLEL]`

- **目标**：实现 FastAPI 服务，暴露 REST API
- **涉及文件**：
  - `src/api/__init__.py`
  - `src/api/main.py` — FastAPI app
  - `src/api/routes/tasks.py` — 任务 API
  - `src/api/routes/config.py` — 配置 API（API Key）
  - `src/api/routes/logs.py` — 日志 API
- **实现要点**：
  - `POST /api/tasks` — 创建任务
  - `GET /api/tasks/{id}` — 查询任务状态
  - `GET /api/tasks/{id}/steps` — 查询执行步骤
  - `GET /api/tasks/{id}/logs` — 查询日志
  - `POST /api/config/keys` — 配置 API Key
  - CORS 支持
- **依赖关系**：Task 2.2, Task 3.1
- **验证步骤**：
  - API 可正常启动
  - 通过 curl/httpx 可调用所有端点
- **首先编写的测试**：
  ```python
  def test_create_task_api(client):
      response = client.post("/api/tasks", json={"description": "fix bug"})
      assert response.status_code == 200
      data = response.json()
      assert "task_id" in data
      assert data["status"] == "pending"
  ```

### Task 4.2：简单前端页面 `[PARALLEL]`

- **目标**：实现基础 Web UI
- **涉及文件**：
  - `web/` 目录下的前端文件
- **实现要点**：
  - 任务创建页面
  - 任务状态页面（轮询更新）
  - 日志查看页面
  - API Key 管理页面
- **依赖关系**：Task 4.1
- **验证步骤**：
  - 页面可正常加载
  - 可完成创建 → 查看 → 查看日志流程
- **首先编写的测试**：手动测试

### Task 4.3：CLI 实现（Typer） `[PARALLEL]`

- **目标**：实现命令行工具
- **涉及文件**：
  - `src/cli/__init__.py`
  - `src/cli/main.py` — Typer app
- **实现要点**：
  - `agent-harness run <description>`
  - `agent-harness status <task_id>`
  - `agent-harness logs <task_id>`
  - `agent-harness config set-key <provider> <key>`
  - 调用 REST API 或直接调用核心模块
- **依赖关系**：Task 2.2, Task 3.1 或 Task 4.1
- **验证步骤**：
  - CLI 命令可正常执行
  - 输出格式清晰
- **首先编写的测试**：
  ```python
  def test_cli_help():
      result = subprocess.run(["agent-harness", "--help"], capture_output=True)
      assert result.returncode == 0
  ```

---

## Phase 5：集成与部署

### Task 5.1：Docker 配置完善 `[PARALLEL]`

- **目标**：完善 Dockerfile 和 docker-compose.yml
- **涉及文件**：
  - `Dockerfile`
  - `docker-compose.yml`
  - `.dockerignore`
- **实现要点**：
  - 多阶段构建（可选）
  - 环境变量注入 API Key
  - 暴露 8000 端口
- **依赖关系**：Task 4.1
- **验证步骤**：
  - `docker build` 成功
  - `docker run` 后可访问 API
- **首先编写的测试**：手动测试

### Task 5.2：端到端集成测试 `[SEQUENTIAL]`

- **前置任务**：Phase 3, Phase 4
- **目标**：编写完整的端到端测试
- **涉及文件**：
  - `tests/test_e2e.py`
- **实现要点**：
  - Mock LLM 下完整流程：创建任务 → 执行 → 查看日志
  - 覆盖成功和失败场景
- **依赖关系**：[Task 3.1, Task 4.1, Task 4.2, Task 4.3]
- **验证步骤**：
  - 端到端测试全部通过
- **首先编写的测试**：
  ```python
  async def test_e2e_full_flow(tmp_path):
      # 完整 Mock LLM 测试：创建任务 → Agent Loop → 检查结果 → 检查日志
      pass
  ```

### Task 5.3：最终验收检查 `[SEQUENTIAL]`

- **前置任务**：所有 task
- **目标**：对照 CHECKLIST.md 逐项验收
- **涉及文件**：
  - CHECKLIST.md（更新状态）
- **实现要点**：
  - 逐一验证所有验收标准
  - 补充缺失项
- **依赖关系**：所有 Task
- **验证步骤**：CHECKLIST.md 全部标记为完成

---

## 依赖关系图

```
Phase 0 ──→ Phase 1 ──→ Phase 3 ──→ Phase 5
                │                       │
                └──→ Phase 2 ────→ Phase 4 ──┘
```

**并行组**：
- Phase 0：Task 0.1, 0.2, 0.3 可并行
- Phase 1：Task 1.1, 1.2, 1.3 可并行
- Phase 2：Task 2.1, 2.2 可并行（依赖 Phase 1 或可提前）
- Phase 4：Task 4.1, 4.2, 4.3 可并行

**顺序依赖**：
- Task 3.1（Agent Loop）依赖 Task 1.1, 1.2, 1.3, 2.2
- Task 5.2（E2E 测试）依赖 Phase 3 和 Phase 4
- Task 5.3（验收）依赖所有 Task