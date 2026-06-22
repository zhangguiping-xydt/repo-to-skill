# Contributing to repo-to-skill

Thanks for helping improve repo-to-skill.

repo-to-skill turns repository source code and a user goal into reviewable, callable agent skills. Contributions are most useful when they keep that core workflow safe, testable, and easy to understand.

## Development setup

```bash
python -m pip install -e '.[dev]'
```

Run the standard local checks before opening a pull request:

```bash
python -m pytest -q
ruff check .
```

Run the packaged callable-bundle eval when changing API detection, selection, rendering, validation, or CLI behavior:

```bash
repo-to-skill eval --case callable-bundle-multistack
```

## Contribution guidelines

- Keep generated skills separate from the target repository; repo-to-skill must not modify the repository it analyzes.
- Do not hard-code endpoints, tokens, internal URLs, or machine-local paths in generated outputs.
- Keep generated callers safe by default: dry-run first, explicit endpoint configuration, and explicit execution.
- Add or update tests for behavior changes.
- Prefer small, focused pull requests with clear verification notes.
- Avoid adding remote LLM, embedding, database, or network dependencies to the deterministic core.

## Useful areas to improve

- Additional source-based API detection for common frameworks.
- Better goal-to-interface selection quality.
- Stronger validation for generated skill packages.
- More fixture-based eval cases.
- Documentation that helps agents and humans review generated skills.

## Reporting issues

When reporting a bug, include:

- The command you ran.
- The target stack or framework if known.
- The expected behavior.
- The actual output or error.
- Whether the target repository has API docs, OpenAPI specs, or only source code.

Please do not include private source code, secrets, internal URLs, or access tokens in public issues.
