"""Inspect local PLCopen XML through the structural reader used by PLC-TGV.

Run: python inspect_plcopen.py path/to/project.xml

The JSON describes syntax, program units and LD wiring. It makes no safety
judgment. Warnings cover structural issues visible to this report only.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
from xml.etree import ElementTree as ET

from plcdefuser.plcopen import parse_plcopen
from plcdefuser.st_parser import walk_statements


def local(tag):
    return tag.rsplit("}", 1)[-1]


def inspect(source):
    root = ET.parse(source).getroot()
    if local(root.tag) != "project":
        raise ValueError("The document root is not a PLCopen project")
    raw_pous = [element for element in root.iter() if local(element.tag) == "pou"]
    program = parse_plcopen(source)
    warnings = []
    pous = []
    duplicates = Counter(pou.name.casefold() for pou in program.pous)
    for name, count in sorted(duplicates.items()):
        if count > 1:
            warnings.append(f"Duplicate POU name: {name} ({count})")
    if not raw_pous:
        warnings.append("No POU declarations found")
    for raw, pou in zip(raw_pous, program.pous):
        bodies = [body for body in raw if local(body.tag) == "body"]
        languages = [local(node.tag) for body in bodies for node in body]
        unsupported = sorted({language for language in languages if language not in ("ST", "LD")})
        if not languages:
            warnings.append(f"{pou.name}: no program body")
        if unsupported:
            warnings.append(f"{pou.name}: unrepresented body languages: {', '.join(unsupported)}")
        if len(languages) > 1:
            warnings.append(f"{pou.name}: multiple bodies; the structural reader selects one")
        statements = Counter(st.kind for st in walk_statements(pou.statements))
        if statements["raw"]:
            warnings.append(f"{pou.name}: {statements['raw']} unclassified ST statements")
        ld_ids = Counter(node.local_id for node in pou.ld_elements)
        for key, number in sorted(ld_ids.items()):
            if number > 1:
                warnings.append(f"{pou.name}: duplicate LD localId {key}")
        references = [ref for node in pou.ld_elements for ref in node.all_input_refs]
        dangling = sum(ref not in ld_ids for ref in references)
        if dangling:
            warnings.append(f"{pou.name}: {dangling} LD references have no source element")
        pous.append({
            "name": pou.name, "pou_type": pou.pou_type, "body_languages": languages,
            "parsed_language": pou.language, "variables": len(pou.variables),
            "st_statement_kinds": dict(sorted(statements.items())),
            "ld_element_kinds": dict(sorted(Counter(node.kind for node in pou.ld_elements).items())),
            "ld_element_count": len(pou.ld_elements), "ld_input_reference_count": len(references),
        })
    return {"pou_count": len(pous), "pous": pous, "structural_warnings": warnings}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xml", type=Path)
    args = parser.parse_args()
    try:
        result = inspect(args.xml)
    except (OSError, ValueError, ET.ParseError) as exc:
        parser.exit(1, f"Cannot inspect {args.xml}: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
