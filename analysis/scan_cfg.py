"""Single-scan control-flow graph and guard/data dependencies."""
from __future__ import annotations

from dataclasses import dataclass, field

from st_syntax import names


@dataclass
class ScanNode:
    kind: str
    expression: tuple | None = None
    target: str | None = None
    closes: tuple[int, ...] = ()
    successors: list[tuple[int, bool | None]] = field(default_factory=list)


def build_scan_cfg(statements):
    """Lower structured ST to a single-scan CFG in topological order.

    The scan model handles persistence between SCAN EXIT and the next entry.
    Branch edges record their outcome even when both lead to the same join.
    """
    nodes = [ScanNode('entry')]

    def add(node, incoming):
        index = len(nodes)
        nodes.append(node)
        for predecessor, outcome in incoming:
            nodes[predecessor].successors.append((index, outcome))
        return index

    def lower(block, incoming):
        for statement in block:
            if statement[0] == 'assign':
                _, target, expression = statement
                tail = add(ScanNode('assign', expression, target), [incoming])
            elif statement[0] == 'if':
                _, branches, otherwise = statement
                ends, guards = [], []
                for condition, body in branches:
                    guard = add(ScanNode('guard', condition), [incoming])
                    guards.append(guard)
                    ends.append(lower(body, (guard, True)))
                    incoming = (guard, False)
                ends.append(lower(otherwise, incoming))
                tail = add(ScanNode('join', closes=tuple(guards)), ends)
            else:
                raise ValueError(f'Unsupported CFG statement: {statement[0]}')
            incoming = (tail, None)
        return incoming

    add(ScanNode('exit'), [lower(statements, (0, None))])
    return nodes


def assignment_dependencies(cfg, declarations):
    """Collect RHS reads and guard reads along the CFG, merging by variable."""
    dependencies = {name: set() for name in declarations}
    active_guards = [set() for _ in cfg]
    reads = [names(node.expression) if node.expression is not None else set() for node in cfg]
    for index, node in enumerate(cfg):
        guards = active_guards[index]
        if node.kind == 'guard':
            guards.add(index)
        elif node.kind == 'join':
            guards.difference_update(node.closes)
        elif node.kind == 'assign':
            dependencies[node.target].update(reads[index])
            for guard in guards:
                dependencies[node.target].update(reads[guard])
        for successor, _ in node.successors:
            active_guards[successor].update(guards)
    return dependencies


def property_dependencies(dependencies, property_names):
    """Close the property-variable set over data and guard dependencies."""
    relevant = set(property_names)
    pending = list(relevant)
    while pending:
        newly_relevant = dependencies[pending.pop()] - relevant
        pending.extend(newly_relevant)
        relevant.update(newly_relevant)
    return relevant
