from __future__ import annotations

from repo_to_skill.models import CapabilityEvidence, CapabilityGraph, SkillSpec, VerificationReport


def verify_static_outputs(evidence: CapabilityEvidence, graph: CapabilityGraph, spec: SkillSpec) -> VerificationReport:
    findings: list[str] = []
    if not evidence.evidence:
        findings.append("FAIL: capability evidence is empty")
    else:
        findings.append("PASS: capability evidence is non-empty")

    if not graph.nodes:
        findings.append("FAIL: capability graph has no nodes")
    else:
        findings.append("PASS: capability graph is non-empty")

    if not spec.name:
        findings.append("FAIL: skill spec is missing name")
    else:
        findings.append("PASS: skill spec has name")

    if not spec.description:
        findings.append("FAIL: skill spec is missing description")
    else:
        findings.append("PASS: skill spec has description")

    if not spec.capabilities:
        findings.append("FAIL: skill spec has no capabilities")
    else:
        findings.append("PASS: skill spec has capabilities")

    boundary_text = " ".join(spec.safety_boundaries).lower()
    if spec.local_first and "writes artifacts only" in boundary_text and "reads only" in boundary_text:
        findings.append("PASS: safety boundary is local-first")
    else:
        findings.append("FAIL: safety boundary is not local-first")

    status = "FAIL" if any(finding.startswith("FAIL") for finding in findings) else "PASS"
    return VerificationReport(status=status, findings=findings)
