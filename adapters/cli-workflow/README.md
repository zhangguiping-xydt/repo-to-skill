# CLI Workflow Adapter

Use this adapter when an AI coding agent can follow local command workflows and reference generated files, but does not need native package registration.

## When to use

Choose this adapter when the target tool can:

- read local markdown context
- run user-approved local commands
- inspect repository files
- keep command output visible for review

## File mapping

| repo-to-skill output | CLI workflow role |
|---|---|
| `SKILL.md` | Main workflow guide |
| `manifest.yaml` | Command and safety metadata reference |
| `scripts/inspect_repo.py` | Optional read-only inspection helper |
| `scripts/common.py` | Shared helper code for generated scripts |
| `references/` | Evidence and review material |

## Suggested workflow

```bash
repo-to-skill validate ./generated-skill
python ./generated-skill/scripts/inspect_repo.py ./target-repo
```

Only run helper scripts after reviewing `manifest.yaml` and confirming the command is read-only.

## Command wrapper layout

Use text command recipes when the target tool can present named local commands for user approval:

```text
<tool-config>/
├── context/
│   └── repo-to-skill.md
└── commands/
    ├── validate-skill.txt
    └── inspect-repo.txt
```

`validate-skill.txt`:

```bash
repo-to-skill validate ./generated-skill
```

`inspect-repo.txt`:

```bash
python ./generated-skill/scripts/inspect_repo.py ./target-repo
```

These files are recipes for reviewed local execution, not automatic background registration.

## Adapter rules

- Keep generated helper scripts opt-in.
- Show command output to the user or calling agent.
- Do not install dependencies as part of this adapter.
- Do not call network services as part of this adapter.
- Do not write into the target repository.
- Do not register background runtime behavior automatically.

## Review checklist

Before using this adapter, confirm:

- `repo-to-skill validate` passes.
- `SKILL.md` describes commands that match the target repository.
- `references/confidence-report.md` does not show unresolved high-risk claims.
- Helper scripts are used for inspection only.
