from __future__ import annotations

from repo_to_skill.models import CapabilityGraph, ProjectProfile, SkillSpec


def build_skill_spec(profile: ProjectProfile, graph: CapabilityGraph) -> SkillSpec:
    capabilities = [node.label for node in graph.nodes]
    commands = profile.test_commands + profile.run_commands + profile.entrypoints
    return SkillSpec(
        name=profile.name,
        description=profile.description or f"Local skill spec for {profile.name}.",
        capabilities=capabilities,
        local_first=True,
        safety_boundaries=[
            "Reads only the target repository during analysis.",
            "Writes artifacts only to the configured output directory.",
            "Does not require CapabilityRegistry, FastAPI, runtime hot registration, remote databases, or vector stores.",
        ],
        commands=commands,
    )
