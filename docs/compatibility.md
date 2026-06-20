# Compatibility

repo-to-skill produces a portable AI coding agent skill pack. The generated output is intentionally plain files: a manifest, `SKILL.md`, read-only helper scripts, and reviewable references.

The core package is not tied to one agent runtime. Different tools can import the same repository knowledge by mapping the generated files into their own workspace-rule, skill, command, or context mechanisms.

## Portability model

The canonical output stays the same across tools:

- `manifest.yaml` records identity and local-first safety boundaries.
- `SKILL.md` describes purpose, commands, workflows, validation, and safety notes.
- `scripts/` contains read-only inspection helpers.
- `references/` contains project map, capability graph, skill spec, and confidence report.

Adapters should translate this output into a target runtime layout without changing the meaning of the generated skill pack.

## Compatibility levels

| Level | Meaning | Expected adapter behavior |
|---|---|---|
| Level 0: Readable | The tool can read markdown or local files as context. | Point the tool at `SKILL.md` and selected `references/` files. |
| Level 1: Structured | The tool supports project instructions, workspace rules, or reusable context files. | Map `SKILL.md` to the runtime instruction entry and keep references alongside it. |
| Level 2: Command-aware | The tool can expose named commands or local helper scripts. | Register read-only commands from `manifest.yaml` and `scripts/` while preserving safety metadata. |
| Level 3: Native package | The tool has a formal skill/package extension format. | Convert the generated pack into that native format through an adapter, with explicit validation before use. |

## Adapter contract

Every adapter must preserve these boundaries:

- local-first usage by default
- no source upload requirement
- no remote database requirement
- no vector database requirement by default
- helper scripts are read-only
- no network from generated helpers
- no dependency installation from generated helpers
- generated helpers do not spawn shell commands
- no writes to the target repository
- no automatic runtime registration without user review

Adapters may add runtime-specific metadata, but they should not remove safety notes or verification references.

## Recommended import flow

1. Generate a skill pack with `repo-to-skill generate` or `repo-to-skill compose`.
2. Review `SKILL.md`, `manifest.yaml`, and `references/confidence-report.md`.
3. Choose the closest adapter under `adapters/`.
4. Copy or map files into the target tool's local project configuration area.
5. Run `repo-to-skill validate` before trusting the mapped output.
6. Keep generated output under review like any other project documentation.

## Neutral layout examples

### Project instruction file layout

Use this when a tool reads one primary project instruction file:

```text
<project-config>/
└── repo-to-skill.md        # copy or link generated SKILL.md
```

Keep `references/` beside the generated skill pack and point the instruction file to those references.

### Workspace context folder layout

Use this when a tool can read a folder of local context files:

```text
<workspace-context>/
├── SKILL.md
├── manifest.yaml
└── references/
    ├── project-map.md
    ├── capability-graph.md
    ├── skill-spec.md
    └── confidence-report.md
```

Do not expose `scripts/` as executable actions unless the tool supports explicit user review for local commands.

### CLI wrapper layout

Use this when a tool can show named local commands for user approval:

```text
<tool-config>/
├── context/
│   └── repo-to-skill.md
└── commands/
    ├── validate-skill.txt       # repo-to-skill validate <generated-skill>
    └── inspect-repo.txt         # python <generated-skill>/scripts/inspect_repo.py <target-repo>
```

Command wrappers should be text recipes or reviewed local commands, not background registrations.

## Current adapters

- [`adapters/generic-markdown`](../adapters/generic-markdown/) for tools that accept markdown project context.
- [`adapters/cli-workflow`](../adapters/cli-workflow/) for tools that can run local CLI workflows but do not need native package registration.

These adapters are intentionally vendor-neutral. They describe file mappings and safety checks without naming specific platforms.
