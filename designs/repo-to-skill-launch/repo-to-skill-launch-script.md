# repo-to-skill Launch Video Script

Format: 16:9, 1920×1080, approximately 70 seconds  
Route: Product narrative version  
Language: English primary, Chinese support copy

## Timing Overview

- 0–8s: Opening
- 8–18s: Problem
- 18–30s: Local analysis
- 30–42s: Skill generation
- 42–52s: Validation and safety
- 52–62s: Real CLI
- 62–70s: Closing

## Full Script

### 0–8s — Opening

**On-screen headline**  
Turn any repository into an AI coding agent skill pack.

**Chinese support copy**  
将任意仓库转化为可复用的 AI 编程代理技能包。

**Voiceover**  
What if your repository could explain how it should be used?

**Visual direction**  
A repository folder opens into clean knowledge cards, then resolves into an AI coding agent skill pack card.

---

### 8–18s — Problem

**On-screen headline**  
Project knowledge is usually scattered.

**Chinese support copy**  
项目知识常常分散在文档、脚本、命令和约定里。

**Voiceover**  
Every project has operating knowledge: setup steps, scripts, test commands, release habits, and safety rules. But that knowledge is often hard to find, hard to transfer, and easy to forget.

**Visual direction**  
Show docs, package files, scripts, test commands, and notes floating as separate cards. The assistant context remains incomplete until the cards start to organize.

---

### 18–30s — Local analysis

**On-screen headline**  
Local-first repository analysis.

**Chinese support copy**  
本地优先分析，不上传仓库。

**Safety badges**  
Local-first · No upload · No remote DB

**Voiceover**  
repo-to-skill analyzes the repository locally. No upload. No remote database. Your project stays where it is.

**Visual direction**  
A closed local loop surrounds the repository. Source files, commands, and docs are read as local signals. Avoid any cloud upload visual metaphor.

---

### 30–42s — Skill generation

**On-screen headline**  
Generate a reviewable AI coding agent skill pack.

**Chinese support copy**  
生成可审阅、可修改、可复用的 AI 编程代理技能包。

**Voiceover**  
It turns those local signals into a structured AI coding agent skill pack: what the project does, how to run it, how to validate it, and what to be careful with.

**Visual direction**  
Cards merge into an editable skill document. Highlight sections such as Purpose, Commands, Workflows, Validation, and Safety Notes.

---

### 42–52s — Validation and safety

**On-screen headline**  
Validate before you trust it.

**Chinese support copy**  
先验证，再信任。

**Safety badges**  
No default vector DB · Reviewable Skill · validate PASS · eval PASS

**Voiceover**  
The result is not a black box. Review the skill, validate it, and run evals. When the checks pass, you have a safer starting point for real coding-agent workflows.

**Visual direction**  
Show a simple validation panel. The status changes to “validate PASS” and “eval PASS”. Keep the safety badges visible and readable.

---

### 52–62s — Real CLI

**On-screen headline**  
Real CLI. Real workflow.

**Chinese support copy**  
真实 CLI，真实工作流。

**Terminal overlay**

```bash
repo-to-skill analyze ./example-repo
repo-to-skill generate ./example-repo
repo-to-skill validate ./generated-skill
repo-to-skill eval ./generated-skill
```

**Terminal result**

```text
analysis complete
generated reviewable skill
validate PASS
eval PASS
```

**Voiceover**  
Use it from the command line, review what it creates, and bring project-specific knowledge into your assistant workflow.

**Visual direction**  
Show a clean terminal with generic paths only. The generated skill card appears beside the terminal as the validated output.

---

### 62–70s — Closing

**On-screen headline**  
Build project knowledge into your assistant.

**Chinese support copy**  
把项目知识沉淀进你的开发助手。

**Final support line**  
Local-first. No upload. Reviewable. Validated.

**Voiceover**  
repo-to-skill helps turn the way your project works into a skill your assistant can actually use.

**Visual direction**  
Final product loop: repository knowledge becomes a reviewable skill, then becomes better assistant behavior. Hold the final frame long enough to read.

## Short Copy Alternatives

Use these if a shot needs fewer words:

- English: Local-first. Reviewable. Validated.
- Chinese: 本地优先，可审阅，已验证。
- English: No upload. No remote DB. No default vector DB.
- Chinese: 不上传，无远程数据库，默认不使用向量数据库。
- English: From repo signals to skill pack.
- Chinese: 从仓库信号到技能包。

## Publishing Guardrails

- Do not show private machine paths.
- Do not show private network links.
- Do not show access keys, secrets, credentials, or account identifiers.
- Do not imply repository upload.
- Do not imply a remote database requirement.
- Do not imply a default vector database requirement.
- Keep all CLI examples generic and publish-safe.
