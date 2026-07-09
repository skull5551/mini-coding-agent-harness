 REFLECTION.md — 课程反思

 1. Superpowers 技能分析

 brainstorming 的作用

在项目初期，brainstorming 技能用了 7 个步骤把我从"做一个 Coding Agent Harness"这个模糊想法引导到可执行的设计文档。如果没有这个分步引导，我大概率会直接跳到"写一个调用 LLM 的 Agent"，然后发现缺少反馈机制、缺少状态管理、缺少安全设计，最后反复返工。但是对于一个大一学生，开发经验少导致brainstorming过程非常痛苦，因为我也不太清楚到底有哪些可能的场景，必要的功能。

最有用的是第 4 步"明确不做什么"。这个环节让我明确列出"先不做"的功能——不做通用 AI 程序员、不做 Benchmark 平台、不支持多语言。这些边界写在 SPEC 里之后，每次实现时犹豫要不要加功能，看一眼 SPEC 就能刹车。对于课程项目这种时间有限的场景，这个步骤的价值远大于"要做什么"。

不过说实话，第 2 步（目标用户）和第 3 步（使用场景）有大量重叠。目标用户画像里的"开发者关心什么"和使用场景里的"用户遇到什么问题"基本是同一件事从不同角度说。实际写 SPEC 的时候，我把这两步的输出合并了，感觉没必要分开。

### writing-plans 的作用

PLAN.md 是整个项目里被我实际参考最多的文档。它不只是"计划"，而是充当了实现时的检查清单。每个 Task 都列出了"目标 / 涉及文件 / 实现要点 / 依赖 / 验证步骤 / 首先编写的测试"，这个格式让我在开始写代码之前就知道要改哪些文件，不会出现"改了 A 文件才发现 B 文件也需要改"的情况。

依赖关系图（Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5）在实际执行中基本准确。唯一一次偏离是 Phase 4 的 Web UI 和 CLI 并行开发时，CLI 的 `config set-key` 命令需要等 StateManager 的 `save_api_key` 方法完成，但 PLAN 里没标注这个微依赖，导致 CLI 比 API 先写完，但测试时发现 API 端点的接口和 CLI 调用的方法签名不完全一致，花了一点时间对齐。

### subagent-driven-development 的体验

这是我在这个项目里最大的收获之一。课程里说的是"subagent-driven-development"，实际操作时，我把每个 PLAN 中的 Task 当作一个独立的 subagent 任务来处理。每次只关注一个 Task，不操心其他模块。

具体做法是：打开 PLAN 里对应 Task 的描述，先写测试，再实现，通过后跑一下全量测试确认没有回归，然后标记完成。这个流程让我在 Phase 3 写 Agent Loop 时，不需要同时考虑 Phase 4 的 API 怎么设计——因为 PLAN 已经定好了接口，我只需要相信 LLM Provider 的 `chat()` 方法和 ToolRegistry 的 `get()` 方法会按预期工作。

但也有一个教训：当 subagent 处理一个 Task 时，有时候会"偷懒"。比如 Task 1.2（Tool 系统）的 subagent 最初实现 ExecuteCommandTool 时没有加超时控制，这个漏洞在后续的 code review 里才被发现。这说明 subagent 虽然能独立完成任务，但缺乏全局视角，需要 code review 来兜底。

### test-driven-development 的作用

TDD 在这个项目里的作用超出了我的预期。最初我觉得 TDD 主要是为了保证代码正确性，但实际用下来，更大的价值是**设计先行**。写测试时，我必须先想清楚"这个函数的输入是什么、输出是什么、边界情况是什么"，这些思考直接倒逼了接口设计。

最典型的例子是 FeedbackAnalyzer。最初 SPEC 里只说"分析执行结果"，但写测试时我不得不明确：exit_code=0 返回什么？exit_code=1 且 stderr 包含 "FAILED" 返回什么？超时情况怎么判断？这些边界问题在测试里体现出来后，接口设计自然就清晰了。

### code review 的作用

Phase 1 完成后的 code review 发现了 3 个 Critical 问题：

1. `write_file.py` 的 `import os` 写在文件末尾（低级错误，但确实发生了）
2. `execute_command.py` 没有超时控制（如果 Agent 执行了一个死循环命令，会永久阻塞）
3. `RunTestTool` 没有实现，但 SPEC 里明确要求（直接偏离了设计）

这三条如果没被发现，后两个问题会在 Agent Loop 实际运行时导致严重故障。code review 在这里充当了 "subagent 的质量检查员" 角色——subagent 负责快速实现，review 负责找漏洞。

---

## 2. TDD 反思

### TDD 在 AI 协作开发中是阻碍还是放大器？

我的结论是：**放大器**。

TDD 加 AI 协作，好的一面会被放大，坏的一面也会被放大。

好的一面：AI 写测试非常快。我只需要描述"写一个测试，验证 MockLLMProvider 在响应耗尽后抛出 StopIteration"，AI 几秒钟就能生成符合 pytest 风格的测试代码。然后我写实现，AI 跑测试，反馈循环极快。这种节奏下，Phase 1 的 3 个 Task 在一个小时内就全部完成了。

坏的一面：AI 有时候会"为了通过测试而写代码"，而不是"为了正确而写代码"。比如有一个测试用例是 `test_analyze_test_failure`，AI 最初实现的 FeedbackAnalyzer 只检查了 `stderr` 里有没有 "fail" 关键词。Windows 上 pytest 的输出是走 stdout 的，所以这个实现在 Windows 上完全检测不到测试失败。测试本身没问题，但实现太窄了。后来修复为同时检查 stdout 和 stderr 才解决。

这个问题本质上是 TDD 的经典陷阱——"测试通过了不代表代码正确"，但 AI 协作放大了这个陷阱，因为 AI 会倾向于最小化修改来让测试变绿。

### Mock LLM 测试为什么重要？

Mock LLM 测试是整个项目可测试性的基石。没有它，Agent Loop 的测试要么依赖真实 LLM API（不稳定、有成本、慢），要么根本没法测。

具体来说，Mock LLM 解决了三个问题：

1. **确定性**：LLM 输出有随机性，同一个 prompt 可能返回不同结果。Mock LLM 每次返回完全相同的 JSON，测试结果可重复。我重复运行了三次全量测试，结果完全一致。

2. **速度**：76 个测试全部跑完只要 6 秒。如果每个测试都调用真实 API，即使最快的模型也要几十秒起步。

3. **场景覆盖**：Mock LLM 可以模拟各种极端场景——Agent 选择了不存在的工具、Agent 返回了格式错误的 JSON、Agent 连续 20 步都不完成。这些场景用真实 LLM 很难触发。

但 Mock LLM 也有局限：它只能测试"机制是否正确"，不能测试"LLM 是否真的理解任务"。Agent Loop 的流程正确不等于 Agent 真正有用。最终演示还是需要用真实 LLM 跑一次，验证整体效果。

---

## 3. Agent 工作流反思

### subagent 可以自主运行多久？

在我这个项目里，单个 subagent 处理的 Task 大约需要 10-30 分钟。最短的是 Task 1.1（Mock LLM Provider），5 个测试 + 实现，10 分钟。最长的是 Task 3.1（Agent Loop），7 个测试 + 126 行实现 + 跟 4 个依赖模块的集成，约 30 分钟。

但"自主运行"有个前提：PLAN 里的 Task 描述必须足够精确。Task 1.2（Tool 系统）的 PLAN 写得很详细，列出了每个文件、每个测试用例的代码示例，subagent 执行得非常顺畅。相比之下，Task 4.2（前端页面）的 PLAN 只说"实现基础 Web UI"，subagent 执行时出现了多次方向性偏差，需要人工介入纠正。

### 哪些 task 粒度最合适？

回顾整个项目，我觉得最合适的粒度是：**一个 Task = 一个模块的一个完整功能 + 对应的测试**。

具体来说：
- Task 1.1（LLM Provider 抽象 + Mock LLM）：粒度刚好，一个文件 + 5 个测试
- Task 1.2（Tool 系统 + 4 个工具）：偏大，8 个文件 + 11 个测试，应该拆成"Tool 抽象层"和"具体工具实现"两个 Task
- Task 4.2（Web UI）：偏大且模糊，没有明确拆解

教训是：如果一个 Task 涉及超过 3 个文件，就应该考虑拆分。如果一个 Task 的 PLAN 描述超过 20 行，也可能是粒度过大的信号。

### SPEC/PLAN 如何影响实现质量？

SPEC 和 PLAN 对实现质量的影响是结构性的，不是线性的。我发现一个规律：**SPEC 里用具体例子说明的接口，实现质量最高；SPEC 里只有一句话带过的功能，实现时最容易出问题**。

FeedbackAnalyzer 是一个好例子：SPEC 附录 D 给出了完整的输入输出示例（`{"success": false, "error_type": "test_failure", "detail": "..."}`），实现时直接照着这个格式写，一次通过。而 Logger 模块在 SPEC 里只有一句"使用 structlog"，实际实现时发现 structlog 的依赖太重在 Windows 上安装有问题，最终没有引入，日志功能通过 SQLite 的 ExecutionStep 表间接实现了。

这说明：SPEC 不仅是"需求文档"，更是"实现参考"。越具体的接口定义，越能减少实现时的决策成本。

---

## 4. Prompt/Context Engineering

在本项目中，Agent Loop 的 system prompt 是唯一需要手工设计的 prompt。它的内容如下：

```
You are a coding agent. You have access to the following tools:
- read_file
- write_file
- execute_command
- run_test

Respond with JSON in one of these formats:
{"action": "tool_call", "tool": "<name>", "params": {...}}
{"action": "done", "reason": "..."}
{"action": "failed", "reason": "..."}
```

这个 prompt 有效的原因：

1. 格式约束明确：给出了三种 JSON 格式的具体示例，LLM 不需要猜测输出格式。Agent Loop 的 `_parse_decision` 方法只处理这三种格式，其他格式返回 None 并请求重试。
2. 工具列表动态生成：prompt 中的工具列表来自 `ToolRegistry.list_tools()`，不是写死的。如果未来新增工具，prompt 自动更新。
3. 每种 action 的结果明确：tool_call 表示执行操作，done 表示任务完成，failed 表示任务失败。LLM 不需要用自然语言描述"我完成了"，一个 JSON 字段就够了。
4. 简洁：整个 prompt 不到 10 行。Agent 的上下文窗口有限，每多一行 system prompt，就少一行给任务描述和反馈信息。
在实现过程中，我注意到一个细节：Action 的三种状态设计（tool_call / done / failed）直接决定了 Agent Loop 的终止逻辑。如果设计成只有 tool_call 和 done 两种，Agent 在遇到无法解决的问题时只能无限循环或被步数限制强制终止。failed 状态让 Agent 可以主动声明"我做不到"，这对可靠性和用户体验都有帮助。

---

## 5. 工程要求反思

### API Key 安全要求迫使自己考虑了什么？

在实现 API Key 管理之前，我的直觉是"把 Key 写在环境变量里就行"。但课程要求明确说"不硬编码 key、不显示明文、支持更新和删除"，这迫使我重新思考整个存储和展示流程。

具体来说，我考虑了以下几个问题：

1. 存储隔离：API Key 不能和 Task 数据混在一起。虽然都放在 SQLite 里，但 ApiKey 表有独立的 CRUD 接口，API 端点也单独挂在 `/api/config/keys` 下。
2. 掩码展示：`get_api_keys()` 返回的不是 `key_value`，而是 `key_masked`。掩码规则是 `sk-****abcd` 格式，首 3 个字符 + 4 个星号 + 尾 4 个字符。这个设计让我意识到：暴露给前端的和存储在后端的必须是两个不同的字段。
3. 明文传输：CLI 的 `config set-key` 命令接受明文 Key 作为参数，这意味着 Key 会出现在命令行历史里。这是目前的安全弱点，但考虑到课程项目的范围，暂时没有做更复杂的输入方式。
4. 环境变量注入：Docker 部署时通过 `HARNESS_API_KEY_OPENAI` 环境变量注入，这个方案比 Web UI 录入更安全，因为环境变量不会出现在任何持久化存储中（除了 Docker 的 inspect 命令）。
### Docker/CI/部署要求发现了哪些问题？

Docker 构建过程中，我发现了一个在本地开发时完全不会遇到的问题：`pyproject.toml` 里的 `[project.scripts]` 配置没问题，但 `pip install -e "."` 在 Docker 里会报错，因为 `-e` 模式需要完整的 git 仓库信息。解决方案是在 Dockerfile 里用 `pip install -e ".[dev]"` 而不是 `pip install "."`，因为 `-e` 安装时 src 目录结构必须正确。

CI 配置方面，GitHub Actions 的 `pytest tests/` 在 Ubuntu 上运行，发现了一个平台差异：`test_feedback.py` 里的一个测试在 Windows 上通过但在 Linux 上也有类似问题（pytest 输出到 stderr 而非 stdout）。这让我意识到 FeedbackAnalyzer 同时检查 stdout 和 stderr 的设计是正确的，背后其实是被平台差异驱动的。

---

## 6. Superpowers 

### 它假设了什么？

Superpowers 方法论的核心假设是：**一个清晰的 SPEC + 一个详细的 PLAN + 独立的 subagent 执行 = 高质量的交付物**。

这个等式隐含了几个前提：
1. SPEC 和 PLAN 的质量足够高，接口定义足够精确
2. subagent 能独立理解并执行 PLAN 中的 Task
3. 人工介入（code review）能有效地发现 subagent 的遗漏
4. 项目从开始到结束，需求不会发生重大变化

### 哪些假设成立？

假设 1 和 3 在我的项目中得到了验证。SPEC 越详细的地方，实现质量越高（FeedbackAnalyzer 的 JSON 格式示例直接指导了实现）。Code review 确实发现了 3 个 Critical 问题，证明了人工检查的必要性。

假设 4 也基本成立，因为课程项目有明确的验收标准，不像真实项目那样需求会频繁变更。

### 哪些地方不足？

假设 2（subagent 独立执行）的成立是有条件的。在我的项目中，PLAN 写得越详细的 Task，subagent 执行越顺畅；PLAN 描述模糊的 Task（如 Web UI），subagent 出现了方向性偏差。这说明 subagent 的自主性取决于 PLAN 的精确度，但 PLAN 不可能覆盖所有细节——否则 PLAN 本身就成了代码。

另一个不足是：**方法论没有考虑跨 Task 的集成问题**。每个 Task 单独测试通过，但集成到一起时可能出现接口不匹配。比如 Agent Loop 期望 `ToolRegistry.get()` 返回的 tool 有 `execute()` 方法，但 PLAN 里没有明确要求所有 Tool 必须实现 `BaseTool` 基类。这个假设在集成时没有出问题，纯粹是因为 TDD 阶段每个 Tool 都写了测试，测试里自然调用了 `execute()`，间接保证了接口一致性。

### 总结

Superpowers 方法论对于课程项目这种范围明确、时间有限的场景非常有效。它把"做一个 Coding Agent"这个模糊任务分解成了可独立执行的 Task，并且通过 TDD + code review 保证了每个 Task 的质量。

但它不是银弹。如果项目需求本身还在演化，或者 Team 成员之间需要频繁协商接口，那么 SPEC 和 PLAN 的维护成本会急剧上升。在这种情况下，可能更适合先用轻量级设计文档快速迭代，等接口稳定后再补正式的 SPEC 和 PLAN。

---

## 个人收获

Coding Agent 本身的能力取决于 LLM 的智能程度，但 Harness 的可靠性取决于工程机制——步数限制、反馈循环、路径隔离、状态管理。这些机制不是让 Agent 更聪明，而是让 Agent 更可控。
另一个收获是对 TDD 的重新认识。以前我觉得 TDD 是"先写测试再写代码"，但这次实践下来，TDD 更大的价值是"设计检查"——写测试的过程强迫我思考接口的边界条件，这些思考直接影响了代码质量。