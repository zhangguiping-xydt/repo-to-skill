# repo-to-skill

[English](README.md) | [简体中文](README.zh-CN.md)

**Give your AI coding agent a map of the repository before it starts editing.**

repo-to-skill is a local-first CLI that reads a local repository and generates a separate, portable skill pack — project map, key modules, module relationships, task entry points, and validation guidance — so an agent starts oriented instead of guessing.

![Before and after: an AI coding agent working with and without a repo map](docs/assets/repo-to-skill-before-after.svg)

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-3776AB.svg)](pyproject.toml)
[![Release](https://img.shields.io/badge/release-v0.1.1-2EA9C0.svg)](https://github.com/zhangguiping-xydt/repo-to-skill/releases/latest)

- **Local-first** — your source never leaves your machine; no remote services.
- **Non-invasive** — it never modifies the target repository.
- **Deterministic** — static analysis only; no LLM or vector database in the core.
- **Proven at scale** — verified on a large repository with 4,459 files and about 940k scanned lines.

```bash
pip install -e .
repo-to-skill compose ../my-app --output ../my-app-skill
```

## Overview

![repo-to-skill local workflow: local repo, read-only scan, reasoning map, skill pack](docs/assets/repo-to-skill-overview.svg)

The project is built for local scanning: it reads files from a repository on your machine, writes analysis artifacts and generated skill output to directories you choose, and does not upload source code. It does not require a remote database. It also does not use a vector database by default; a vector index may be explored later as an optional extension, but it is not an MVP dependency.

## What it generates

repo-to-skill reads a target repository without modifying it, then generates a separate skill package that an AI coding agent can review and import:

- `SKILL.md` for the human-readable project briefing.
- `manifest.yaml` for package metadata and safety boundaries.
- `references/project-map.md` for modules, representative paths, relationships, task entry points, and validation guidance.
- `references/capability-graph.md` for the capability graph.
- `references/skill-spec.md` for the skill spec.
- `references/confidence-report.md` for capability evidence and verification notes.
- `scripts/inspect_repo.py` as a read-only helper; generated helpers do not spawn shell commands.

The analysis artifact chain includes `scan.json`, `profile.json`, `capability_evidence.json`, `capability_graph.json`, `skill_spec.yaml`, `verification_report.json`, and `confidence-report.md`.

## Visual demo assets

The launch video sources live in [`designs/repo-to-skill-launch`](designs/repo-to-skill-launch/). Large rendered videos are attached to GitHub Releases instead of committed directly into source history.

- [Watch the launch video](https://github.com/zhangguiping-xydt/repo-to-skill/releases/download/v0.1.0/repo-to-skill-launch.mp4)
- [Open the release page](https://github.com/zhangguiping-xydt/repo-to-skill/releases/tag/v0.1.0)

## Installation

From a source checkout:

```bash
python -m pip install -e .
repo-to-skill --help
```

For development checks:

```bash
python -m pip install -e .[dev]
python -m pytest
```

## Quick start from a source checkout

Use the packaged tiny example to see the complete local flow:

```bash
repo-to-skill doctor
repo-to-skill analyze ./examples/tiny-python-app --output ./.runs/tiny-python
repo-to-skill generate ./examples/tiny-python-app --analysis ./.runs/tiny-python --output ./.runs/tiny-python-skill
repo-to-skill validate ./.runs/tiny-python-skill
repo-to-skill compose ./examples/tiny-python-app --output ./.runs/tiny-python-composed-skill --workdir ./.runs/tiny-python-compose
repo-to-skill eval --case tiny-python
```

## Use your own repository

Keep generated analysis and skill output outside the target repository:

```bash
mkdir -p ../repo-to-skill-runs
repo-to-skill compose ../my-app \
  --workdir ../repo-to-skill-runs/my-app-analysis \
  --output ../repo-to-skill-runs/my-app-skill
repo-to-skill validate ../repo-to-skill-runs/my-app-skill
```

Review `SKILL.md`, `manifest.yaml`, and `references/confidence-report.md` before importing the generated skill pack into any AI coding agent environment.

## Commands

- `doctor` checks the local Python/package environment only.
- `analyze` performs local scanning and writes the artifact chain.
- `generate` turns a complete artifact chain into a skill directory.
- `validate` checks the generated skill shape and safety boundaries.
- `compose` runs analyze -> generate -> validate locally without runtime registration.
- `eval` runs deterministic local eval cases such as the packaged `tiny-python` case.

## Safety model

repo-to-skill does not modify the target repository. The analyze/generate output must be outside the target repository so generated artifacts never become accidental source changes.

Generated helper scripts are read-only: no network, no dependency installation, and generated helpers do not spawn shell commands. They inspect checked-in files and render human-reviewable references.

## Scale and limits

repo-to-skill is designed for small to large local repositories. It has been verified on a large enterprise repository with 4,459 scanned files, about 940k scanned lines, and about 569k source lines.

There is no hard total-line limit. Actual runtime depends on file count, disk speed, and how much generated content is present. The scanner skips binary files, symlinks, sensitive files, generated artifacts, dependency folders, local run artifacts, and individual files larger than 1 MiB.

## Compatibility

The generated package is intentionally vendor-neutral. Different tools can read the Markdown references directly, use a command-aware adapter, or implement a native package adapter. See the adapter contract in [Compatibility](docs/compatibility.md) and [Adapters](adapters/README.md).

## Runtime boundary

The open-source version adopts useful repository knowledge ideas: artifact chain, capability evidence, capability graph, skill spec, and verification report. It does not connect to CapabilityRegistry/FastAPI/runtime hot registration, and it is not multi-agent-dev external_skills hot loading.

## More documentation

- [Architecture](docs/architecture.md)
- [Security](docs/security.md)
- [Skill output format](docs/skill-output-format.md)
- [Compatibility](docs/compatibility.md)
- [Adapters](adapters/README.md)
- [Evals](docs/evals.md)

## License and attribution

repo-to-skill is licensed under the Apache License 2.0. You may use, modify, and distribute it under that license.

When redistributing this project or derivative works, retain `LICENSE` and `NOTICE` and include attribution to the repo-to-skill project as the original source.
