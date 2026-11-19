"""Analyze the manifest-verified normal controls using the archived source components."""
import argparse
import hashlib
import json
from pathlib import Path

from scalar_model import TypedProgram
from scan_cfg import assignment_dependencies, build_scan_cfg, property_dependencies
from st_syntax import names, properties_ast
from state_check import closure


ROOT = Path(__file__).resolve().parent
INDEX = ROOT / 'controls' / 'index.json'


def read_input(entry):
    path = (ROOT / entry['path']).resolve()
    if ROOT / 'controls' not in path.parents:
        raise ValueError('Invalid input path in control index')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != entry['sha256']:
        raise ValueError('Input hash mismatch for ' + entry['path'])
    return raw.decode('utf-8-sig')


def analyze(case_id, entry, state_limit):
    program = TypedProgram(read_input(entry['source']))
    specs = json.loads(read_input(entry['properties']))['properties']
    if not specs or any(spec['kind'] not in ('invariant', 'mutual_exclusion') for spec in specs):
        raise ValueError('Expected an invariant or mutual exclusion property')
    expressions = properties_ast(specs)
    roots = set().union(*(names(node) for node in expressions))
    if not roots <= program.declarations.keys():
        raise ValueError('Undeclared property variable')
    graph = build_scan_cfg(program.statements)
    dependencies = assignment_dependencies(graph, program.declarations)
    return {
        'id': case_id,
        'cfg_nodes': len(graph),
        'cfg_edges': sum(len(node.successors) for node in graph),
        'requirements': [spec['id'] for spec in specs],
        'property_variables': sorted(roots),
        'property_dependencies': sorted(property_dependencies(dependencies, roots)),
        'state_limit': state_limit,
        'finite_state_audit': closure(program, expressions, cap=state_limit),
    }


def main():
    cases = json.loads(INDEX.read_text(encoding='utf-8'))['controls']
    parser = argparse.ArgumentParser(description=__doc__)
    selected = parser.add_mutually_exclusive_group(required=True)
    selected.add_argument('--all', action='store_true', help='analyze all eight controls')
    selected.add_argument('--case', choices=sorted(cases), help='analyze a single control')
    parser.add_argument('--state-limit', type=int, default=256,
                        help='maximum retained states in the finite-state audit (default: 256)')
    args = parser.parse_args()
    if args.state_limit < 1:
        parser.error('--state-limit must be positive')
    try:
        ids = sorted(cases) if args.all else [args.case]
        report = [analyze(key, cases[key], args.state_limit) for key in ids]
    except (ArithmeticError, ValueError, KeyError, OSError) as exc:
        parser.exit(1, 'Analysis failed: ' + str(exc) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
