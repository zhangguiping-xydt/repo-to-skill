# 工作原理

repo-to-skill 把一个本地源码仓库和一句用户目标，转换成一个可安装的可调用 agent skill——不需要 API 文档、不需要 OpenAPI spec、不需要运行时抓包。这份文档解释这条流水线背后的工作原理：每一阶段为什么存在、产出什么、确定性工具与生成阶段 agent 判断之间的边界在哪里。

## 核心前提

大多数遗留系统与内部系统里已经锁着很有价值的行为：HR 流程、财务审批、排班引擎、报表接口。这些行为藏在 HTTP 接口背后，而 coding agent 没法靠自己安全地复用——读得懂源码不等于能安全地调用线上系统。

repo-to-skill 桥接的就是这一段。它把源码仓库当作事实来源（source of truth），产出一个独立的、可审阅的 skill 包，让另一个 agent 可以去调用。工作原理贯彻四条承诺：

1. **从源码出发，不从文档出发**。通过静态分析源码来检测可调用接口，不依赖 API 文档或 OpenAPI spec。这让本工具恰好能用在那些最缺文档的系统上：老旧的内部系统与企业服务。
2. **以目标为驱动**。用户给一句自然语言目标，工具按相关性打分挑出最匹配的接口，而不是逼用户自己去点 API 名字。
3. **设计上非侵入**。目标仓库只读。所有分析产物与生成的 skill 一律写到目标仓库之外。
4. **每阶段可审计**。每一阶段都产出持久化检查点（JSON/YAML/Markdown）。选中的接口都带分数、理由和源码出处。审阅者随时能查到每个接口为什么被选中、每个字段在源码哪一行被定义。

## 流水线

```text
目标仓库 + 用户目标
   │
   ▼
1. analyze    （静态扫描 → 产物链）
   │
   ▼
2. select     （按目标对可调用接口打分选型）
   │
   ▼
3. generate   （产物链 + 选型 → skill 包）
   │
   ▼
4. validate   （必填文件、安全元数据、路径泄漏、禁用 token）
   │
   ▼
5. install    （可选：复制到 ~/.claude/skills、~/.agents/skills）
```

`analyze`、`generate`、`validate` 也可以通过本地一条 `compose` 命令一起跑。`eval` 跑针对同一条流水线的确定性本地回归用例。

## 阶段一 — analyze（分析）

`repo-to-skill analyze <repo> --output <workdir>/analysis` 读仓库，产出一条显式产物链：

- `scan.json` —— 文件清单，带确定性剪枝（跳过二进制、符号链接、敏感文件、依赖目录、生成产物、单文件 > 1 MiB）。
- `profile.json` —— 语言、生态、主技术栈、项目名。
- `capability_evidence.json` —— 关于代码做了什么的 claim，每条都绑到源码路径。
- `capability_graph.json` —— 能力及其关系。
- `skill_spec.yaml` —— 提议的 skill 能力。
- `verification_report.json` —— 静态检查 evidence 是否真的支持 claim。
- `confidence-report.md` —— 人类可读的 evidence 与置信度说明。
- `callable_capabilities.json` —— 可调用接口目录（HTTP 方法、路由、handler 符号、handler 路径/行号、business method、请求/响应契约、endpoint env、token env、副作用、置信度）。

可调用接口检测是多技术栈的：Java/Spring、C#/.NET、Python（FastAPI/Flask/Django/Tornado）以及其它 HTTP 框架都从源码检测，不从描述文件。每个接口都追溯到具体 handler，请求/响应模型从源码类型定义（Java POJO/record、C# 属性、Python dataclass/Pydantic 模型）解析出来。

这一阶段**完全是确定性的**。不调 LLM、不需要联网、不修改目标仓库。

## 阶段二 — select（选型）

选型拿一句用户目标，决定检测出的接口里哪些进生成的 skill。这里分两层。

### 确定性打分器

打分器是一个 TF-IDF 风格的排序器，实现在 `repo_to_skill/skillgen/callable_selector.py`。它把用户目标切成 token，再对每个接口的各元数据字段做匹配，按字段本身的区分度加权：

| 字段 | 权重 | 说明 |
|------|------|------|
| `slug` | 4.0 | 直接标识符——最强信号。 |
| `handler_symbol` | 3.5 | 源码里的函数名。区分度高。 |
| `route` | 3.0 | URL 路径往往承载业务语义。 |
| `business_method` | 3.0 | handler 调用的命名 service 方法。 |
| `request_fields` | 2.5 | 单个字段名命中目标词汇。 |
| `request_model` / `response_model` | 2.0 | 类型名。 |
| `response_fields` | 2.0 | 与请求同含义，但对意图的预测力略低。 |
| `framework` / `stack` | 1.0 | 弱信号——主要用于 tie-breaking。 |
| `side_effects` | 0.5 | 近乎零权重——为了完整性保留。 |

IDF 在检测出的接口目录里算，所以出现在很多接口里的 token（例如 `get`、`list`）被打折，而罕见业务词（例如 `overtime`、`leave_balance`）主导排序。Top-N 接口（`callable-bundle` 默认 `--max-interfaces 12`，`callable-composite` 默认 5）成为确定性 fallback 选型。

### Agent override

当生成阶段 agent 有把握说出正确的 slug，它通过 `--selected-slugs`（或 `--selection-json`）覆盖打分器。此时 skill 产物里记录 `selection_source: agentic`，每个 item 分数 `1.0`、理由 `"selected by agent slug"`。

对未知 slug **fail-loud**：如果 agent 说了一个不在 `callable_capabilities.json` 里的 slug，工具直接抛 `unknown callable interface slug: <slug>`，不会悄悄丢掉。这防止 agent 捏造源码里根本不存在的 API。

### 两种选型模式

- **`callable-bundle`** —— 选 N 个接口，每个都暴露一个独立能力，每个变成一个独立的 tool。适合"给我一个干 X 的工具箱"。
- **`callable-composite`** —— 选 2–N 个接口组成线性链（A→B→C），至少 2 个。适合"算出一个需要按顺序调多个 API 才能得到的最终答案"。

## 阶段三 — generate（生成）

生成阶段根据分析产物和选型，渲染三种 skill kind 之一：

- **`repo-map`** —— 只读导览包，没有 live 调用。适合目标是探索而不是执行。
- **`callable-bundle`** —— 一个 skill 目录，包含：
  - `tools/*.tool.yaml` —— 每个 API 一份机器可读 tool 契约。
  - `scripts/call_*.py` —— 每个 API 一份安全 caller 脚本。
  - `references/capability-selection.md` —— 每个 API 为什么被选中。
  - `references/capability-source.md` —— 源码级出处（路由、handler、business method、字段）。
- **`callable-composite`** —— 在 bundle 布局之上加一份 `orchestrator.py` 和 `references/composition.md`。orchestrator 按固定顺序串接 caller，并在 step 之间插 `# TODO: fill from step_<n>.<field>` 标记。

每个生成的 caller **默认预览模式**：只有用户设置了 endpoint 环境变量并传 `--execute` 时才真的发 HTTP 请求。token 从环境变量读，在预览输出里做脱敏。caller 永远不硬编码 endpoint 或 token。

生成器**是确定性的**。不调 LLM。输入只有分析产物、选型、以及 `repo_to_skill/skillgen/templates/` 下的 Jinja 模板。

## 阶段四 — validate（校验）

校验是一道结构性安全闸，不是风格检查。它强制：

- 每种 skill kind 的必填文件（例如 composite 必须有 `orchestrator.py`、至少 2 个 tool、至少 2 个 caller 脚本、tools/scripts 数量一致）。
- manifest 正确性（`kind`、`composition.goal`、`composition.steps`、`runtime.interfaces_count`）。
- orchestrator 能 `ast.parse` 通过、含必要的 TODO 标记（标记必须存在，这样生成阶段 agent 才不会把没填字段映射的 composite 发出去）。
- 每个 caller 的禁用 token（`subprocess`、裸 `open()`、可写 open 模式）。网络访问只允许 `urllib.request` / `urllib.error`。
- 生成的 skill 不泄漏机器路径（`/home/`、`/tmp/`、`/media/`、绝对路径、内部 URL、凭据）。

校验失败会阻断后续 install。这里把校验当成一份**契约**：校验通过，这个 skill 在结构上就是可安全安装和审阅的。

## 阶段五 — install（安装，可选）

`--install` 把生成的 skill 复制到 `~/.claude/skills` 和 `~/.agents/skills`，方便跨 agent 使用。install 不会自动注册到任何运行时 hot-loader、capability registry 或 MCP server。skill 就是一组文件，用户的 coding agent 在 session 启动时读它。

## 生成阶段 agent 的角色

repo-to-skill 在每一处影响安全与结构正确性的阶段都是确定性的。生成阶段 agent（例如 Claude Code）只在两个具体环节贡献判断：

1. **Slug 选型**。当确定性打分器的 Top-N 跟用户真实目标对不上时，agent 用 `--selected-slugs` 覆盖。agent 先读 `references/capability-source.md` 理解每个接口的业务语义，再做选择。
2. **Composite 字段映射**。对 `callable-composite`，agent 读 `references/composition.md`，理解 step N-1 的哪些响应字段必须流到 step N 的请求里，然后把 `orchestrator.py` 里的 `# TODO: fill from step_<n>.<field>` 标记替换成具体代码。这一步在没有源码级数据流追踪的前提下做不到确定性，超出 MVP 范围。

其它任何地方，agent 都不覆盖工具。工具的分析、选型打分、安全校验、结构检查是权威的。

## 与 Business SkillOps 的关系

本项目和 Business SkillOps 是同一作者。这里的透明产物流（artifact chain、capability evidence、capability graph、skill spec、verification report）就是 Business SkillOps 里同一套设计。开源版 repo-to-skill 流水线**不**连接 CapabilityRegistry、FastAPI 运行时或热注册系统。生成的 skill 是本地文件，由人显式审阅、安装、校验。

## 为什么对遗留系统有效

遗留系统几乎从没有 API 文档，但几乎一定有带 HTTP handler 签名和类型化请求/响应模型的源码。把源码当作事实来源，repo-to-skill 恰好能用在那些 doc-driven / spec-driven 工具够不着的系统上。确定性流水线还意味着：同一个仓库分析两次，生成的 skill 一致——这是文档抓取类方案做不到的属性。

## 边界小结

- repo-to-skill 不修改目标仓库。
- 不需要 API 文档、OpenAPI spec 或网络抓包。
- 在分析、选型、生成、校验任何环节都不调 LLM。
- 不会把生成的 skill 自动注册到任何运行时或 capability registry。
- 不会自动追踪源码级数据流；composite 把字段映射留成 TODO 给生成阶段 agent。
- 生成的 caller 默认预览；live HTTP 调用必须显式配置 endpoint 并传 `--execute`。
