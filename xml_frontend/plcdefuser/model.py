from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class Variable:
    name: str
    datatype: str
    storage: str
    initial: Optional[str] = None


@dataclass
class Statement:
    kind: str
    text: str
    line: int
    condition: Optional[str] = None
    lhs: Optional[str] = None
    rhs: Optional[str] = None
    callee: Optional[str] = None
    children: List["Statement"] = field(default_factory=list)
    branches: List[Tuple[str, List["Statement"]]] = field(default_factory=list)


@dataclass
class LDElement:
    local_id: str
    kind: str
    type_name: Optional[str] = None
    instance_name: Optional[str] = None
    variable: Optional[str] = None
    expression: Optional[str] = None
    negated: bool = False
    inputs: Dict[str, List[str]] = field(default_factory=dict)

    @property
    def all_input_refs(self) -> List[str]:
        refs: List[str] = []
        for values in self.inputs.values():
            refs.extend(values)
        return refs


@dataclass
class POU:
    name: str
    pou_type: str
    variables: Dict[str, Variable]
    language: str
    statements: List[Statement] = field(default_factory=list)
    ld_elements: List[LDElement] = field(default_factory=list)
    raw_body: str = ""

    @property
    def input_names(self) -> List[str]:
        return [v.name for v in self.variables.values() if v.storage == "input"]

    @property
    def local_names(self) -> List[str]:
        return [v.name for v in self.variables.values() if v.storage in {"local", "temp"}]


@dataclass
class PLCProgram:
    source: Path
    pous: List[POU]

    @property
    def pou_names(self) -> List[str]:
        return [p.name for p in self.pous]


@dataclass
class CFGNode:
    node_id: str
    pou: str
    kind: str
    instruction: str = ""
    line: Optional[int] = None
    metadata: Dict[str, object] = field(default_factory=dict)


@dataclass
class CFGEdge:
    source: str
    target: str
    condition: str = "TRUE"
    kind: str = "flow"


@dataclass
class CFG:
    pou: str
    nodes: Dict[str, CFGNode] = field(default_factory=dict)
    edges: List[CFGEdge] = field(default_factory=list)
    entry: str = ""
    termination: str = ""

    def add_node(self, node: CFGNode) -> None:
        self.nodes[node.node_id] = node

    def add_edge(self, source: str, target: str, condition: str = "TRUE", kind: str = "flow") -> None:
        self.edges.append(CFGEdge(source=source, target=target, condition=condition or "TRUE", kind=kind))


@dataclass
class TriggerFinding:
    kind: str
    pou: str
    node_id: str
    condition: str
    evidence: str
    path_conditions: List[str] = field(default_factory=list)


@dataclass
class LoopCheck:
    pou: str
    condition: str
    variable: Optional[str]
    update: Optional[str]
    verdict: str
    reason: str
    witness: Optional[Dict[str, object]] = None


@dataclass
class LoopTransitionModel:
    """Serializable bounded transition model produced from one ST WHILE."""

    pou: str
    inputs: List[str]
    initial_values: Dict[str, Optional[str]]
    path_assignments: List[Tuple[str, str]]
    path_guards: List[str]
    loop_condition: str
    loop_variable: Optional[str]
    loop_updates: List[Tuple[str, str]]
    mutated_outputs: List[str]
    unsupported_reason: Optional[str] = None
