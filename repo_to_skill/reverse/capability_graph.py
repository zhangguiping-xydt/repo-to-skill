from __future__ import annotations

from repo_to_skill.models import CapabilityEdge, CapabilityEvidence, CapabilityGraph, CapabilityNode


def build_capability_graph(capability_evidence: CapabilityEvidence) -> CapabilityGraph:
    nodes = [
        CapabilityNode(
            id=f"capability:{item.name}",
            label=item.name.replace("_", " "),
            kind=item.kind,
            confidence=item.confidence,
        )
        for item in capability_evidence.evidence
    ]
    nodes = sorted(nodes, key=lambda node: node.id)
    edges: list[CapabilityEdge] = []
    node_ids = [node.id for node in nodes]
    for node_id in node_ids:
        if node_id != "capability:configuration" and "capability:configuration" in node_ids:
            edges.append(CapabilityEdge(source="capability:configuration", target=node_id, relation="supports"))
    if "capability:package_manager" in node_ids and "capability:test" in node_ids:
        edges.append(CapabilityEdge(source="capability:package_manager", target="capability:test", relation="runs"))
    if "capability:entrypoint" in node_ids and "capability:cli" in node_ids:
        edges.append(CapabilityEdge(source="capability:entrypoint", target="capability:cli", relation="exposes"))
    edges = sorted({(edge.source, edge.target, edge.relation): edge for edge in edges}.values(), key=lambda edge: (edge.source, edge.target, edge.relation))
    return CapabilityGraph(nodes=nodes, edges=edges)
