"""Neurosymbolic Failure Knowledge Graph (KCoEvo Graph).

Constructs directed causal graphs of negative constraints connecting
mechanisms, root causes, and prohibited AST transformations.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List


class FailureKnowledgeGraph:
    def __init__(self):
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Dict[str, str]] = []

    def add_constraint(self, mechanism: str, root_cause: str, prohibited_action: str):
        mech_id = f"M_{mechanism.lower().replace(' ', '_')}"
        cause_id = f"C_{root_cause.lower().replace(' ', '_')[:20]}"
        act_id = f"A_{prohibited_action.lower().replace(' ', '_')[:20]}"

        self.nodes[mech_id] = {"type": "mechanism", "label": mechanism}
        self.nodes[cause_id] = {"type": "root_cause", "label": root_cause}
        self.nodes[act_id] = {"type": "prohibition", "label": prohibited_action}

        self.edges.append({"from": mech_id, "to": cause_id, "rel": "causes"})
        self.edges.append({"from": cause_id, "to": act_id, "rel": "prohibits"})

    def to_mermaid(self) -> str:
        lines = ["graph LR"]
        for node_id, data in self.nodes.items():
            lbl = data["label"].replace('"', "'")
            if data["type"] == "mechanism":
                lines.append(f'  {node_id}["⚙️ {lbl}"]')
            elif data["type"] == "root_cause":
                lines.append(f'  {node_id}{{"⚠️ {lbl}"}}')
            else:
                lines.append(f'  {node_id}(["🚫 {lbl}"])')

        for edge in self.edges:
            lines.append(f"  {edge['from']} -->|{edge['rel']}| {edge['to']}")
        return "\n".join(lines)


def main():
    g = FailureKnowledgeGraph()
    g.add_constraint("Global Lock in Thread Loop", "GIL Contention & Deadlock", "Lock-free atomic CAS")
    print(g.to_mermaid())


if __name__ == "__main__":
    main()
