# Adapters

Adapters explain how to map a repo-to-skill output directory into different AI coding agent environments without making the core project depend on one runtime.

The generated skill pack remains the source of truth. Adapter documents describe how to place or reference those files in a target tool.

## Core output

A repo-to-skill output directory contains:

```text
<generated-skill>/
├── manifest.yaml
├── SKILL.md
├── scripts/
│   ├── common.py
│   └── inspect_repo.py
└── references/
    ├── project-map.md
    ├── capability-graph.md
    ├── skill-spec.md
    └── confidence-report.md
```

## Adapter responsibilities

An adapter should define:

- which generated files are imported
- where the target tool should read them from
- whether helper scripts are exposed or only referenced
- what validation must run before use
- what safety boundaries the target tool must preserve

An adapter should not silently broaden permissions, upload source code, install dependencies, or register runtime behavior without review.

## Included adapter patterns

- [`generic-markdown`](generic-markdown/) maps the generated skill pack to tools that read markdown project context.
- [`cli-workflow`](cli-workflow/) maps the generated skill pack to tools that support local command workflows.

## Common neutral layouts

```text
<project-config>/repo-to-skill.md
```

Use this layout when the target tool reads one project instruction file.

```text
<workspace-context>/
├── SKILL.md
├── manifest.yaml
└── references/
```

Use this layout when the target tool reads a context folder.

```text
<tool-config>/commands/
├── validate-skill.txt
└── inspect-repo.txt
```

Use this layout when the target tool exposes reviewed local command recipes.

See [Compatibility](../docs/compatibility.md) for compatibility levels and the adapter contract.
