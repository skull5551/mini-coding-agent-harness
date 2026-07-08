# CHECKLIST.md — 项目验收清单

用于跟踪课程要求完成情况。

## 文档类

| # | 验收项 | 状态 | 备注 |
|---|--------|------|------|
| D1 | SPEC.md 完整 | ☐ | 包含问题陈述、用户故事、功能/非功能规约、安全设计、架构、数据模型、技术选型、验收标准、风险 |
| D2 | PLAN.md 完整 | ☐ | 按 subagent-driven-development 拆分 task，每个 task 含目标/文件/要点/依赖/验证/失败测试 |
| D3 | SPEC_PROCESS.md 完整 | ☐ | 记录 brainstorming 全过程、关键决策、AI 建议、反思 |
| D4 | CHECKLIST.md 完整 | ☐ | 本文档自身 |
| D5 | README.md 完整 | ☐ | 包含项目简介、快速开始、架构图、API 说明 |
| D6 | AGENT_LOG.md 完整 | ☐ | 记录每步 Agent 协作过程 |
| D7 | REFLECTION.md 完整 | ☐ | 课程反思 |

## 核心功能类

| # | 验收项 | 状态 | 备注 |
|---|--------|------|------|
| C1 | Agent Loop 可在 Mock LLM 下完整执行：任务输入 → 分析 → 工具调用 → 反馈 → 完成 | ☐ | |
| C2 | Agent Loop 在超出最大步数时自动终止 | ☐ | |
| C3 | Agent Loop 支持成功/失败/暂停三种终止状态 | ☐ | |
| C4 | LLM Provider 抽象接口定义正确 | ☐ | |
| C5 | MockLLMProvider 支持预设响应序列 | ☐ | |
| C6 | 真实 LLM Provider（litellm）可调用 | ☐ | |
| C7 | Tool Executive 支持读文件、写文件、执行命令、运行测试 | ☐ | |
| C8 | Tool 拒绝路径遍历攻击 | ☐ | |
| C9 | ToolRegistry 支持工具注册和查找 | ☐ | |
| C10 | Feedback Analyzer 正确分析测试失败/成功 | ☐ | |
| C11 | Feedback Analyzer 正确识别错误类型 | ☐ | |

## 状态与任务管理类

| # | 验收项 | 状态 | 备注 |
|---|--------|------|------|
| S1 | SQLite 数据库自动建表（Task, ExecutionStep, ToolCall, ApiKey） | ☐ | |
| S2 | 创建 Task 后可在 DB 中查询 | ☐ | |
| S3 | Task 生命周期完整：pending → running → success/failed/paused | ☐ | |
| S4 | 执行步骤和工具调用可关联查询 | ☐ | |

## 安全类

| # | 验收项 | 状态 | 备注 |
|---|--------|------|------|
| K1 | API Key 不硬编码在代码中 | ☐ | |
| K2 | API Key 通过 Web UI 录入，不显示明文 | ☐ | |
| K3 | API Key 支持更新和删除 | ☐ | |
| K4 | 未配置 Key 时无法调用真实 LLM（有提示） | ☐ | |
| K5 | API 接口不返回 Key 明文 | ☐ | |

## Web UI 类

| # | 验收项 | 状态 | 备注 |
|---|--------|------|------|
| W1 | Web UI 可启动，可访问 | ☐ | |
| W2 | 任务创建页面可用 | ☐ | |
| W3 | 任务状态页面可查看实时状态 | ☐ | |
| W4 | 日志页面可查看 Agent 执行步骤 | ☐ | |
| W5 | API Key 管理页面可用 | ☐ | |

## CLI 类

| # | 验收项 | 状态 | 备注 |
|---|--------|------|------|
| L1 | `agent-harness run <description>` 可创建任务 | ☐ | |
| L2 | `agent-harness status <task_id>` 可查询状态 | ☐ | |
| L3 | `agent-harness logs <task_id>` 可查看日志 | ☐ | |
| L4 | `agent-harness --help` 显示帮助信息 | ☐ | |

## 测试类

| # | 验收项 | 状态 | 备注 |
|---|--------|------|------|
| T1 | pytest 可运行，全部测试通过 | ☐ | |
| T2 | Mock LLM 单元测试覆盖所有 Agent Loop 核心场景 | ☐ | |
| T3 | Tool 单元测试覆盖读写文件和命令执行 | ☐ | |
| T4 | Feedback Analyzer 单元测试覆盖成功/失败 | ☐ | |
| T5 | 状态管理单元测试覆盖 CRUD | ☐ | |
| T6 | API 集成测试覆盖主要端点 | ☐ | |
| T7 | Mock LLM 测试结果可重复（三次运行一致） | ☐ | |

## 部署类

| # | 验收项 | 状态 | 备注 |
|---|--------|------|------|
| E1 | Dockerfile 构建成功 | ☐ | |
| E2 | Docker 容器启动后 API 可访问 | ☐ | |
| E3 | 环境变量注入 API Key 有效 | ☐ | |
| E4 | CI 配置在 push 后自动运行 pytest | ☐ | |

---

## 最终验收

| # | 验收项 | 状态 | 备注 |
|---|--------|------|------|
| ✅ | 所有核心功能测试通过 | ☐ | |
| ✅ | 所有文档完整 | ☐ | |
| ✅ | Docker 可部署 | ☐ | |
| ✅ | API Key 安全 | ☐ | |
| ✅ | Web UI 可用 | ☐ | |
| ✅ | CLI 可用 | ☐ | |