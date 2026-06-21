from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


class DumpMixin:
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def model_dump(self) -> dict[str, Any]:
        return self.to_dict()


@dataclass
class FileRecord(DumpMixin):
    path: str
    size: int
    line_count: int
    sha256: str
    language: str
    role: str


@dataclass
class ScanResult(DumpMixin):
    root: str
    files: list[FileRecord] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    ecosystems: list[str] = field(default_factory=list)
    package_managers: list[str] = field(default_factory=list)
    candidate_commands: list[str] = field(default_factory=list)
    entrypoints: list[str] = field(default_factory=list)
    git: dict[str, Any] = field(default_factory=dict)


@dataclass
class Evidence(DumpMixin):
    name: str
    kind: str
    summary: str
    sources: list[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class Claim(DumpMixin):
    name: str
    description: str
    evidence: list[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class ModuleSummary(DumpMixin):
    name: str
    total: int
    source: int
    configuration: int
    documentation: int
    test: int
    languages: list[str] = field(default_factory=list)
    signals: list[str] = field(default_factory=list)
    summary: str = ""
    representative_paths: list[str] = field(default_factory=list)


@dataclass
class ModuleRelationship(DumpMixin):
    source: str
    target: str
    relation: str
    reason: str
    evidence: list[str] = field(default_factory=list)


@dataclass
class TaskGuideItem(DumpMixin):
    task: str
    start_with: list[str] = field(default_factory=list)
    then_check: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass
class ValidationGuideItem(DumpMixin):
    scope: str
    commands: list[str] = field(default_factory=list)
    paths: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class ProjectProfile(DumpMixin):
    name: str
    description: str
    primary_language: str
    languages: list[str] = field(default_factory=list)
    ecosystems: list[str] = field(default_factory=list)
    package_managers: list[str] = field(default_factory=list)
    test_commands: list[str] = field(default_factory=list)
    run_commands: list[str] = field(default_factory=list)
    entrypoints: list[str] = field(default_factory=list)
    configuration_files: list[str] = field(default_factory=list)
    documentation_files: list[str] = field(default_factory=list)
    source_files: list[str] = field(default_factory=list)
    test_files: list[str] = field(default_factory=list)
    module_summaries: list[ModuleSummary] = field(default_factory=list)
    module_relationships: list[ModuleRelationship] = field(default_factory=list)
    task_entry_guide: list[TaskGuideItem] = field(default_factory=list)
    validation_guide: list[ValidationGuideItem] = field(default_factory=list)


@dataclass
class CapabilityEvidence(DumpMixin):
    project: str
    evidence: list[Evidence] = field(default_factory=list)
    claims: list[Claim] = field(default_factory=list)


@dataclass
class CapabilityNode(DumpMixin):
    id: str
    label: str
    kind: str
    confidence: float


@dataclass
class CapabilityEdge(DumpMixin):
    source: str
    target: str
    relation: str


@dataclass
class CapabilityGraph(DumpMixin):
    nodes: list[CapabilityNode] = field(default_factory=list)
    edges: list[CapabilityEdge] = field(default_factory=list)


@dataclass
class SkillSpec(DumpMixin):
    name: str
    description: str
    capabilities: list[str] = field(default_factory=list)
    local_first: bool = True
    safety_boundaries: list[str] = field(default_factory=list)
    commands: list[str] = field(default_factory=list)


@dataclass
class VerificationReport(DumpMixin):
    status: str
    findings: list[str] = field(default_factory=list)


@dataclass
class IoField(DumpMixin):
    name: str
    type: str = "unknown"
    required: bool = False
    description: str = ""
    source_path: str = ""
    source_symbol: str = ""
    confidence: float = 0.0


@dataclass
class IoContract(DumpMixin):
    model_name: str = "unknown"
    media_type: str = "application/json"
    fields: list[IoField] = field(default_factory=list)
    confidence: float = 0.0
    unresolved: bool = True
    notes: list[str] = field(default_factory=list)


@dataclass
class CallableInterface(DumpMixin):
    id: str
    slug: str
    stack: str
    framework: str
    transport: str = "http"
    http_method: str = "UNKNOWN"
    route: str = ""
    handler_symbol: str = ""
    handler_path: str = ""
    handler_line: int = 0
    business_method: str = ""
    request: IoContract = field(default_factory=IoContract)
    response: IoContract = field(default_factory=IoContract)
    endpoint_env: str = ""
    token_env: str = ""
    auth_required: bool = True
    side_effects: str = "unknown"
    confidence: float = 0.0
    evidence: list[str] = field(default_factory=list)


@dataclass
class CallableCapabilitySet(DumpMixin):
    project: str
    interfaces: list[CallableInterface] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
