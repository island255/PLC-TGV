"""Finite-state closure audit for Boolean inputs and typed scalar state."""
from collections import deque
import itertools


def closure(program, properties, cap=5000):
    inputs = [n for n, d in program.declarations.items() if d["input"]]
    retained = [n for n, d in program.declarations.items() if not d["input"]]
    if any(program.declarations[n]["type"] != "BOOL" for n in inputs) or len(inputs) > 8:
        return {"verdict": "UNSUPPORTED", "reason": "Boolean input envelope"}
    assignments = [dict(zip(inputs, v)) for v in itertools.product((False, True), repeat=len(inputs))]
    initial = program.initial()
    first = tuple(initial[n] for n in retained)
    seen = {first}
    queue = deque([first])
    count = 0
    while queue:
        key = queue.popleft()
        env = dict(initial)
        env.update(zip(retained, key))
        for inputs_now in assignments:
            post = program.step(env, inputs_now)
            count += 1
            values = [program.evaluate(prop, post) for prop in properties]
            if any(type(v) is not bool for v in values):
                raise ValueError("The safety requirement must evaluate to BOOL")
            if not all(values):
                return {"verdict": "VIOLATION", "reachable_states": len(seen),
                        "transitions": count}
            nxt = tuple(post[n] for n in retained)
            if nxt not in seen:
                if len(seen) >= cap:
                    return {"verdict": "UNKNOWN", "reason": "State cap", "reachable_states": len(seen), "transitions": count}
                seen.add(nxt)
                queue.append(nxt)
    return {"verdict": "SAFE", "reachable_states": len(seen), "transitions": count,
            "evidence": "Complete reachable-state closure for the given program and property"}
