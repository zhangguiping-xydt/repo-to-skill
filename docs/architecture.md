# Architecture

repo-to-skill is a local-first CLI. It performs local scanning of a target repository and does not upload source code. All inputs and outputs stay on the user's machine unless the user separately decides to share them.

## Pipeline

1. `doctor` checks local runtime readiness.
2. `analyze` reads a local repository and emits an artifact chain.
3. `generate` converts the artifact chain into a reviewable AI coding agent skill pack.
4. `validate` checks required files, safety metadata, helper script restrictions, and path leaks.
5. `compose` runs analyze -> generate -> validate in one local command.
6. `eval` runs deterministic local regression cases.

## Analysis artifacts

The artifact chain is explicit and reviewable:

- `scan.json`
- `profile.json`
- `capability_evidence.json`
- `capability_graph.json`
- `skill_spec.yaml`
- `verification_report.json`
- `confidence-report.md`

The design intentionally uses capability evidence, capability graph, skill spec, and verification report as durable checkpoints between stages.

## Storage model

repo-to-skill does not require a remote database. It writes normal files to local output directories.

repo-to-skill does not use a vector database by default. A vector database can be considered later as an optional extension for larger repositories, but it is not required by the MVP architecture.

## Repository write boundary

repo-to-skill does not modify the target repository. The analyze/generate output must be outside the target repository. This keeps generated artifacts, eval workspaces, and skill output separate from source code.

## Business SkillOps boundary

The open-source architecture borrows the transparent artifact flow from Business SkillOps: artifact chain, capability evidence, capability graph, skill spec, and verification report.

It does not connect to CapabilityRegistry/FastAPI/runtime hot registration. It is also not multi-agent-dev external_skills hot loading. Generated skills are local files that humans can review, install, and validate explicitly.
