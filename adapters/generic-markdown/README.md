# Generic Markdown Adapter

Use this adapter when an AI coding agent can read markdown files as project context but does not require a native skill package format.

## When to use

Choose this adapter when the target tool supports one or more of these patterns:

- project instruction files
- workspace context files
- manually attached markdown references
- repository-local assistant notes

## File mapping

| repo-to-skill output | Generic target role |
|---|---|
| `SKILL.md` | Primary instruction/context document |
| `manifest.yaml` | Metadata and safety boundary reference |
| `references/project-map.md` | Project layout reference |
| `references/capability-graph.md` | Capability and workflow reference |
| `references/skill-spec.md` | Structured skill contract reference |
| `references/confidence-report.md` | Review checklist and confidence notes |
| `scripts/` | Keep as local read-only helper references unless the tool explicitly supports safe script execution |

## Import steps

1. Generate the skill pack.
2. Read `SKILL.md` and `references/confidence-report.md` before importing.
3. Copy or link `SKILL.md` into the target tool's local project context area.
4. Keep `references/` near the imported context so the agent can inspect supporting evidence.
5. Do not expose `scripts/` as executable actions unless the target tool supports explicit read-only command review.
6. Run `repo-to-skill validate <generated-skill>` after any adapter-side changes.

## Layout examples

Single instruction file:

```text
<project-config>/
└── repo-to-skill.md        # copied from SKILL.md
```

Context folder:

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

## Safety notes

This adapter is read-oriented. It should preserve:

- no source upload requirement
- no remote database requirement
- no default vector database requirement
- helper scripts are read-only
- no network from generated helpers
- no dependency installation from generated helpers
- generated helpers do not spawn shell commands

If a target tool asks for broader permissions, treat that as a separate manual review step rather than part of this adapter.
