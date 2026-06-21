from __future__ import annotations

import importlib
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from repo_to_skill import __version__
from repo_to_skill.evals.runner import run_eval
from repo_to_skill.reverse.callable_capabilities import build_callable_capabilities
from repo_to_skill.reverse.capability_evidence import build_capability_evidence
from repo_to_skill.reverse.capability_graph import build_capability_graph
from repo_to_skill.reverse.confidence_report import build_confidence_report
from repo_to_skill.reverse.project_profile import build_project_profile
from repo_to_skill.reverse.skill_spec import build_skill_spec
from repo_to_skill.reverse.verification import verify_static_outputs
from repo_to_skill.scanner.filesystem import scan_repository
from repo_to_skill.skillgen.planner import plan_callable_bundle, plan_callable_skills, plan_skill
from repo_to_skill.skillgen.renderer import render_callable_bundle, render_callable_skills, render_skill
from repo_to_skill.skillgen.validator import SkillValidationReport, validate_skill
from repo_to_skill.workspace.paths import resolve_target_and_output
from repo_to_skill.workspace.store import ArtifactStore

app = typer.Typer(help="Local-first repository-to-skill tooling.")
console = Console()


@app.callback()
def cli() -> None:
    """Local-first repository-to-skill tooling."""


def _run_analysis(target: Path, output: Path) -> tuple[Path, str]:
    store = ArtifactStore(target, output)
    scan = scan_repository(store.target_root)
    profile = build_project_profile(scan, store.target_root)
    evidence = build_capability_evidence(profile, scan)
    graph = build_capability_graph(evidence)
    spec = build_skill_spec(profile, graph)
    verification = verify_static_outputs(evidence, graph, spec)
    confidence_report = build_confidence_report(profile, evidence, verification)
    callable_capabilities = build_callable_capabilities(scan, store.target_root)

    store.write_json("scan.json", scan)
    store.write_json("profile.json", profile)
    store.write_json("capability_evidence.json", evidence)
    store.write_json("capability_graph.json", graph)
    store.write_yaml("skill_spec.yaml", spec)
    store.write_json("verification_report.json", verification)
    store.write_markdown("confidence-report.md", confidence_report)
    store.write_json("callable_capabilities.json", callable_capabilities)
    return store.output_root, verification.status


def _print_validation(report: SkillValidationReport) -> None:
    console.print(f"Validation: {report.status}")
    for finding in report.findings:
        console.print(f"- {finding}")


def _generate_skill(target: Path, analysis: Path, output: Path) -> SkillValidationReport:
    target_root, output_root = resolve_target_and_output(target, output)
    plan = plan_skill(target_root, analysis)
    skill_root = render_skill(plan, output_root)
    report = validate_skill(skill_root)
    console.print(f"Generated skill: {skill_root}", soft_wrap=True)
    _print_validation(report)
    return report


def _generate_callable_skills(target: Path, analysis: Path, output: Path) -> bool:
    target_root, output_root = resolve_target_and_output(target, output)
    plan = plan_callable_skills(target_root, analysis)
    if not plan.interfaces:
        console.print("No callable HTTP interfaces detected.")
        return True
    all_pass = True
    for pack in render_callable_skills(plan, output_root):
        report = validate_skill(pack)
        console.print(f"Generated callable skill: {pack}", soft_wrap=True)
        _print_validation(report)
        if report.status != "PASS":
            all_pass = False
    return all_pass


def _parse_slugs(value: str | None) -> list[str] | None:
    if value is None:
        return None
    return [part.strip() for part in value.split(",") if part.strip()]


def _generate_callable_bundle(
    target: Path,
    analysis: Path,
    output: Path,
    *,
    need: str,
    max_interfaces: int,
    selected_slugs: str | None,
    selection_json: Path | None,
) -> bool:
    target_root, output_root = resolve_target_and_output(target, output)
    plan = plan_callable_bundle(
        target_root,
        analysis,
        need=need,
        selected_slugs=_parse_slugs(selected_slugs),
        selection_json=selection_json,
        max_interfaces=max_interfaces,
    )
    bundle = render_callable_bundle(plan, output_root)
    report = validate_skill(bundle)
    console.print(f"Generated callable bundle: {bundle}", soft_wrap=True)
    _print_validation(report)
    return report.status == "PASS"


@app.command()
def analyze(
    target: Path = typer.Argument(..., help="Local repository to analyze."),
    output: Path = typer.Option(..., "--output", "-o", help="Directory for generated artifacts."),
) -> None:
    """Analyze a local repository and write local-first skill artifacts."""
    try:
        output_root, status = _run_analysis(target, output)
    except ValueError as exc:
        console.print(str(exc))
        raise typer.Exit(code=1) from exc

    console.print(f"Analysis complete: {output_root}")
    if status != "PASS":
        raise typer.Exit(code=1)


@app.command()
def generate(
    target: Path = typer.Argument(..., help="Local repository the analysis describes."),
    analysis: Path = typer.Option(..., "--analysis", help="Analysis run directory or profile.json."),
    output: Path = typer.Option(..., "--output", "-o", help="Skill output directory."),
    mode: str = typer.Option(
        "repo-map",
        "--mode",
        help="Skill kind to generate: 'repo-map', 'callable', or 'callable-bundle'.",
    ),
    need: str = typer.Option("", "--need", help="User goal for callable-bundle interface selection."),
    max_interfaces: int = typer.Option(12, "--max-interfaces", help="Maximum callable interfaces in a bundle."),
    selected_slugs: str | None = typer.Option(
        None,
        "--selected-slugs",
        help="Comma-separated callable interface slugs selected by an agent or user.",
    ),
    selection_json: Path | None = typer.Option(
        None,
        "--selection-json",
        help="JSON file with need_summary, selected_slugs, and selection_source.",
    ),
) -> None:
    """Generate a reviewable local AI coding agent skill pack from existing analysis artifacts."""
    if mode not in {"repo-map", "callable", "callable-bundle"}:
        console.print(f"Unknown mode: {mode}; expected 'repo-map', 'callable', or 'callable-bundle'.")
        raise typer.Exit(code=1)
    try:
        if mode == "callable":
            all_pass = _generate_callable_skills(target, analysis, output)
        elif mode == "callable-bundle":
            all_pass = _generate_callable_bundle(
                target,
                analysis,
                output,
                need=need,
                max_interfaces=max_interfaces,
                selected_slugs=selected_slugs,
                selection_json=selection_json,
            )
        else:
            all_pass = _generate_skill(target, analysis, output).status == "PASS"
    except ValueError as exc:
        console.print(str(exc))
        raise typer.Exit(code=1) from exc
    if not all_pass:
        raise typer.Exit(code=1)


@app.command(name="validate")
def validate_command(
    skill_path: Path = typer.Argument(..., help="Skill directory to validate."),
) -> None:
    """Validate a generated skill directory for required shape and safety boundaries."""
    report = validate_skill(skill_path)
    _print_validation(report)
    if report.status != "PASS":
        raise typer.Exit(code=1)


@app.command()
def compose(
    target: Path = typer.Argument(..., help="Local repository to analyze and turn into a skill."),
    output: Path = typer.Option(..., "--output", "-o", help="Skill output directory."),
    workdir: Path = typer.Option(..., "--workdir", help="Analysis work directory."),
) -> None:
    """Run local analyze -> generate -> validate without runtime registration or network use."""
    try:
        analysis_root, status = _run_analysis(target, workdir)
        console.print(f"Analysis complete: {analysis_root}")
        if status != "PASS":
            raise typer.Exit(code=1)
        report = _generate_skill(target, analysis_root, output)
    except ValueError as exc:
        console.print(str(exc))
        raise typer.Exit(code=1) from exc
    if report.status != "PASS":
        raise typer.Exit(code=1)


@app.command(name="eval")
def eval_command(
    case: str = typer.Option(..., "--case", help="Evaluation case name to run."),
    workspace: Path | None = typer.Option(
        None,
        "--workspace",
        help="Optional workspace for eval outputs; defaults to a temporary directory.",
    ),
) -> None:
    """Run deterministic local evals without network, installs, or runtime registration."""
    try:
        result = run_eval(case, workspace)
    except ValueError as exc:
        console.print(str(exc))
        raise typer.Exit(code=1) from exc

    console.print(f"Eval case: {result.case_name}")
    for check in result.checks:
        status = "PASS" if check.passed else "FAIL"
        console.print(f"- {check.name}: {status} — {check.detail}")
    console.print(f"Eval result: {result.status}")
    if not result.passed:
        raise typer.Exit(code=1)


@app.command()
def doctor() -> None:
    """Report local environment checks without network or repository writes."""
    python_ok = sys.version_info >= (3, 11)
    package_dir = Path(__file__).resolve().parent
    package_files_ok = package_dir.exists() and package_dir.is_dir()

    try:
        importlib.import_module("repo_to_skill")
    except ImportError as exc:
        package_import_ok = False
        package_import_detail = str(exc)
    else:
        package_import_ok = True
        package_import_detail = "repo_to_skill"

    table = Table(title=f"repo-to-skill doctor {__version__}")
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Detail")

    table.add_row(
        "Python version",
        "ok" if python_ok else "unsupported",
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    )
    table.add_row(
        "Package import",
        "ok" if package_import_ok else "failed",
        package_import_detail,
    )
    table.add_row(
        "Package files",
        "ok" if package_files_ok else "missing",
        str(package_dir),
    )
    table.add_row(
        "Network access",
        "disabled",
        "doctor performs local checks only",
    )
    table.add_row(
        "Repository writes",
        "disabled",
        "doctor does not write target repositories",
    )

    console.print(table)

    if not python_ok or not package_import_ok or not package_files_ok:
        raise typer.Exit(code=1)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
