# Security Policy

## Supported versions

Security updates are provided for the latest released version of repo-to-skill.

## Reporting a vulnerability

Please report security vulnerabilities privately through GitHub Security Advisories for this repository when available.

If GitHub Security Advisories are not available to you, contact the repository owner through GitHub and avoid posting sensitive details in a public issue.

Please include:

- A description of the vulnerability.
- Steps to reproduce the issue.
- The affected command, generated file, or workflow.
- Any relevant logs with secrets and internal URLs removed.

Do not include private source code, credentials, access tokens, internal endpoints, or customer data in public reports.

## Security expectations

repo-to-skill is designed to analyze local repositories and generate separate skill packages. Security-sensitive behavior should preserve these boundaries:

- Do not modify the target repository during analysis or generation.
- Do not upload source code to external services from the deterministic core.
- Do not write endpoints or tokens into generated skills.
- Generated callable scripts should default to dry-run and require explicit execution.
- Generated output should not expose machine-local paths, private URLs, or credentials.
- Sensitive files such as `.env`, `.env.local`, keys, and certificates should be skipped.

## Public issue guidance

For non-sensitive bugs, please open a normal GitHub issue. For anything involving secrets, credential exposure, unsafe generated code, target repository writes, or source disclosure, use the private reporting path above.
