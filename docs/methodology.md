# How it works

repo-to-skill turns a local source repository and a user goal into an installable callable agent skill — without API docs, OpenAPI specs, or runtime capture. This document explains the methodology behind that pipeline: why each stage exists, what it produces, and where the boundary between deterministic tooling and agent judgment sits.

## Core premise

Most legacy and internal systems already contain valuable behavior: HR workflows, finance approvals, scheduling engines, reporting endpoints. That behavior is locked behind HTTP interfaces that coding agents cannot safely reuse on their own — reading the source code is not the same as calling the live system.

repo-to-skill bridges that gap by treating the source repository as the source of truth and producing a separate, reviewable skill package that another agent can call. The methodology follows four commitments:

1. **Source, not docs.** Static analysis of source code detects callable interfaces. No API documentation or OpenAPI spec is required. This makes the tool usable on exactly the systems that lack docs: older internal and enterprise services.
2. **Goal-oriented selection.** The user gives a natural-language goal. The tool scores and selects the interfaces most likely to serve that goal, instead of asking the user to hand-pick API names.
3. **Non-invasive by construction.** The target repository is read-only. All analysis artifacts and generated skills are written outside the target repository.
4. **Auditable at every stage.** Each stage emits durable checkpoints (JSON/YAML/Markdown). Selections carry scores, reasons, and source provenance. A reviewer can read why each interface was chosen and trace any field back to the file and line that defined it.

## Pipeline

```text
target repository + user goal
   │
   ▼
1. analyze   (static scan → artifact chain)
   │
   ▼
2. select    (goal-based scoring of callable interfaces)
   │
   ▼
3. generate  (artifact chain + selection → skill pack)
   │
   ▼
4. validate  (required files, safety metadata, path leaks, banned tokens)
   │
   ▼
5. install   (optional: copy into ~/.claude/skills, ~/.agents/skills)
```

`analyze`, `generate`, and `validate` can also be run as one local `compose` command. `eval` runs deterministic local regression cases against the same pipeline.

## Stage 1 — analyze

`repo-to-skill analyze <repo> --output <workdir>/analysis` reads the repository and emits an explicit artifact chain:

- `scan.json` — file inventory with deterministic pruning (binary, symlinks, sensitive files, dependency folders, generated artifacts, files > 1 MiB).
- `profile.json` — languages, ecosystems, primary stack, project name.
- `capability_evidence.json` — claims about what the code does, each tied to a source path.
- `capability_graph.json` — capabilities and their relationships.
- `skill_spec.yaml` — proposed skill capabilities.
- `verification_report.json` — static checks that the evidence supports the claims.
- `confidence-report.md` — human-readable evidence and confidence notes.
- `callable_capabilities.json` — the callable interface catalog (HTTP method, route, handler symbol, handler path/line, business method, request/response contracts, endpoint env, token env, side effects, confidence).

The callable interface detection is multi-stack: Java/Spring, C#/.NET, Python (FastAPI/Flask/Django/Tornado), and other HTTP frameworks are detected from source rather than from descriptors. Each interface is traced to a concrete handler and its request/response models are parsed from source-level type definitions (Java POJOs/records, C# properties, Python dataclasses/Pydantic models).

This stage is **deterministic**. It does not call out to an LLM, does not require network access, and does not modify the target repository.

## Stage 2 — select

Selection takes a user goal and decides which of the detected interfaces belong in the generated skill. The methodology here separates two layers:

### Deterministic scorer

The scorer is a TF-IDF-style ranker implemented in `repo_to_skill/skillgen/callable_selector.py`. It tokenizes the user goal and matches tokens against each interface's metadata fields, weighted by how discriminative the field is:

| Field | Weight | Rationale |
|-------|--------|-----------|
| `slug` | 4.0 | Direct identifier — strongest signal. |
| `handler_symbol` | 3.5 | The function name in source. Highly discriminative. |
| `route` | 3.0 | URL path often carries business semantics. |
| `business_method` | 3.0 | Named service method called by the handler. |
| `request_fields` | 2.5 | Individual field names match the goal vocabulary. |
| `request_model` / `response_model` | 2.0 | Type names. |
| `response_fields` | 2.0 | Same as request but slightly less predictive of intent. |
| `framework` / `stack` | 1.0 | Weak signal — mostly tie-breaking. |
| `side_effects` | 0.5 | Near-zero weight — included for completeness. |

IDF is computed across the detected interface catalog, so a token that appears in many interfaces (e.g., `get`, `list`) is discounted, while a rare business term (e.g., `overtime`, `leave_balance`) dominates the ranking. The top-N interfaces (default `--max-interfaces 12` for `callable-bundle`, 5 for `callable-composite`) become the deterministic fallback selection.

### Agent override

When the generating agent can confidently name the right slugs, it passes `--selected-slugs` (or `--selection-json`) to override the scorer. The skill output records `selection_source: agentic` in that case, with each item scored `1.0` and reason `"selected by agent slug"`.

The methodology is intentionally **fail-loud** on unknown slugs: if the agent names a slug that does not appear in `callable_capabilities.json`, the tool raises `unknown callable interface slug: <slug>` rather than silently dropping it. This prevents the agent from inventing APIs that do not exist in the source.

### Two selection modes

- **`callable-bundle`** — selects N interfaces that each expose an independent capability. Each becomes its own tool. Best when the goal is "give me a toolkit for X".
- **`callable-composite`** — selects 2-N interfaces that form a linear chain (A→B→C). Requires at least 2 interfaces. Best when the goal is "compute a final answer that requires calling several APIs in order".

## Stage 3 — generate

Generation renders one of three skill kinds from the analysis artifacts plus the selection:

- **`repo-map`** — a read-only orientation pack. No live calls. Useful when the goal is exploration, not execution.
- **`callable-bundle`** — one skill directory containing:
  - `tools/*.tool.yaml` — one machine-readable tool contract per selected API.
  - `scripts/call_*.py` — one safe caller per selected API.
  - `references/capability-selection.md` — why each API was selected.
  - `references/capability-source.md` — source-level provenance (route, handler, business method, fields).
- **`callable-composite`** — adds an `orchestrator.py` and `references/composition.md` on top of the bundle layout. The orchestrator chains the callers in a fixed order and emits `# TODO: fill from step_<n>.<field>` markers between steps.

Every generated caller **previews by default**. It only sends an HTTP request when the user sets the endpoint environment variable and passes `--execute`. Tokens are read from environment variables and redacted in preview output. No caller hard-codes an endpoint or token.

The generator is **deterministic**. It does not call an LLM. The only inputs are the analysis artifacts, the selection, and the Jinja templates under `repo_to_skill/skillgen/templates/`.

## Stage 4 — validate

Validation is a structural safety gate, not a style check. It enforces:

- Required files for each skill kind (e.g., composite must have `orchestrator.py`, at least 2 tools, at least 2 caller scripts, tools/scripts count match).
- Manifest correctness (`kind`, `composition.goal`, `composition.steps`, `runtime.interfaces_count`).
- Orchestrator AST-parseability and required TODO markers (the marker must exist so the generating agent does not ship a composite with unresolved field mappings).
- Banned tokens in every caller (`subprocess`, bare `open()`, writable open modes). Only `urllib.request` / `urllib.error` are permitted for network access.
- No machine paths leak into the generated skill (`/home/`, `/tmp/`, `/media/`, absolute paths, internal URLs, credentials).

A validation failure blocks downstream install. The methodology treats validation as a **contract**: if the validator passes, the skill is structurally safe to install and inspect.

## Stage 5 — install

Optional. `--install` copies the generated skill into `~/.claude/skills` and `~/.agents/skills` for cross-agent use. Install does not auto-register with any runtime hot-loader, capability registry, or MCP server. The skill is a directory of files that the user's coding agent reads at session start.

## The generating agent's role

repo-to-skill is deterministic at every stage that affects safety and structural correctness. The generating agent (e.g., Claude Code) contributes judgment at two specific points:

1. **Slug selection.** When the deterministic scorer's top-N does not match the user's actual goal, the agent overrides with `--selected-slugs`. The agent reads `references/capability-source.md` to understand each interface's business semantics before choosing.
2. **Composite field mapping.** For `callable-composite`, the agent reads `references/composition.md`, understands which response fields from step N-1 must flow into step N's request, and replaces the `# TODO: fill from step_<n>.<field>` markers in `orchestrator.py` with concrete code. This step cannot be made deterministic without source-level data-flow tracing, which is out of MVP scope.

Everywhere else, the agent does not override the tool. The tool's analysis, selection scoring, safety validation, and structural checks are authoritative.

## Relationship to Business SkillOps

This project and Business SkillOps share the same author. The transparent artifact flow here (artifact chain, capability evidence, capability graph, skill spec, verification report) is the same design used in Business SkillOps. The open-source repo-to-skill pipeline does **not** connect to a CapabilityRegistry, FastAPI runtime, or hot registration system. Generated skills are local files that humans can review, install, and validate explicitly.

## Why this works on legacy systems

Legacy systems rarely have API docs, but they almost always have source code with HTTP handler signatures and typed request/response models. By treating source as the source of truth, repo-to-skill produces callable skills from exactly the systems that are hardest to reach with doc-driven or spec-driven tools. The deterministic pipeline also means the same repository analyzed twice produces the same skill, which is a property doc-scraping approaches cannot match.

## Boundary summary

- repo-to-skill does not modify the target repository.
- It does not require API documentation, OpenAPI specs, or network capture.
- It does not call an LLM at analysis, selection, generation, or validation time.
- It does not auto-register generated skills with any runtime or capability registry.
- It does not trace source-level data flow automatically; composites leave field mappings as TODOs for the generating agent.
- Generated callers default to preview; live HTTP calls require explicit endpoint configuration and `--execute`.
