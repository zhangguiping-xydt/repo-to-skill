# Evals

repo-to-skill evals are deterministic local checks for the repository-to-skill pipeline. They use local scanning and do not upload source code.

## Running evals

```bash
repo-to-skill eval --case tiny-python
```

The `tiny-python` case is packaged with the installed CLI and runs analyze -> generate -> validate in a temporary local workspace by default. Source-tree copies under `evals/cases` and `examples` are retained as readable examples, but the runner uses packaged resources so installed wheels do not depend on a checkout layout.

## What an eval checks

An eval case describes:

- fixture repository
- expected language signals
- expected capabilities
- required analysis artifacts
- required generated skill files
- safety boundaries
- forbidden machine path tokens in generated `SKILL.md` and references

The runner verifies that the artifact chain exists, validation passes, capability evidence and capability graph are represented through the generated references, the skill spec and verification report are present, and generated output does not leak private machine paths.

## Safety boundaries

Evals are local-first. They do not require a remote database, and they do not use a vector database by default. They do not install dependencies, do not use the network, and do not modify the target repository. The analyze/generate output must be outside the target repository.

Generated helper scripts are read-only with no network, no dependency installation, and generated helpers do not spawn shell commands.

## Business SkillOps boundary

The eval pipeline checks the open-source artifact chain, capability evidence, capability graph, skill spec, and verification report. It does not connect to CapabilityRegistry/FastAPI/runtime hot registration, and it is not multi-agent-dev external_skills hot loading.
