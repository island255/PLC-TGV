from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Optional
from xml.etree import ElementTree as ET

from .model import LDElement, PLCProgram, POU, Variable
from .st_parser import parse_st


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _children_named(element: ET.Element, name: str) -> Iterable[ET.Element]:
    return (child for child in list(element) if _local_name(child.tag) == name)


def _first_child_named(element: ET.Element, name: str) -> Optional[ET.Element]:
    return next(_children_named(element, name), None)


def _datatype(variable: ET.Element) -> str:
    type_element = _first_child_named(variable, "type")
    if type_element is None or not list(type_element):
        return "UNKNOWN"
    value = list(type_element)[0]
    if _local_name(value.tag) == "derived":
        return value.get("name", "derived")
    return _local_name(value.tag)


def _initial_value(variable: ET.Element) -> Optional[str]:
    for element in variable.iter():
        if _local_name(element.tag) == "simpleValue" and element.get("value") is not None:
            return element.get("value")
    return None


def _parse_variables(pou: ET.Element) -> Dict[str, Variable]:
    variables: Dict[str, Variable] = {}
    interface = _first_child_named(pou, "interface")
    if interface is None:
        return variables
    storage_by_group = {
        "inputVars": "input",
        "outputVars": "output",
        "localVars": "local",
        "tempVars": "temp",
        "externalVars": "external",
        "inOutVars": "inout",
    }
    for group in list(interface):
        storage = storage_by_group.get(_local_name(group.tag))
        if storage is None:
            continue
        for variable in _children_named(group, "variable"):
            name = variable.get("name")
            if name:
                variables[name] = Variable(
                    name=name,
                    datatype=_datatype(variable),
                    storage=storage,
                    initial=_initial_value(variable),
                )
    return variables


def _text_of_first(element: ET.Element, name: str) -> Optional[str]:
    child = _first_child_named(element, name)
    if child is None:
        return None
    return "".join(child.itertext()).strip()


def _parse_ld(ld: ET.Element) -> List[LDElement]:
    elements: List[LDElement] = []
    for raw in list(ld):
        kind = _local_name(raw.tag)
        local_id = raw.get("localId")
        if not local_id:
            continue
        inputs: Dict[str, List[str]] = {}

        # Blocks attach formal parameters to nested <variable> elements.
        for nested in raw.iter():
            if _local_name(nested.tag) != "variable" or nested.get("formalParameter") is None:
                continue
            formal = nested.get("formalParameter") or ""
            refs = [
                connection.get("refLocalId")
                for connection in nested.iter()
                if _local_name(connection.tag) == "connection" and connection.get("refLocalId")
            ]
            if refs:
                inputs.setdefault(formal, []).extend(refs)

        # Contacts, coils, rails, and variables use direct connection points.
        generic_refs = [
            connection.get("refLocalId")
            for connection in raw.iter()
            if _local_name(connection.tag) == "connection" and connection.get("refLocalId")
        ]
        already = {ref for refs in inputs.values() for ref in refs}
        remaining = [ref for ref in generic_refs if ref not in already]
        if remaining:
            inputs.setdefault("", []).extend(remaining)

        elements.append(
            LDElement(
                local_id=local_id,
                kind=kind,
                type_name=raw.get("typeName"),
                instance_name=raw.get("instanceName"),
                variable=_text_of_first(raw, "variable"),
                expression=_text_of_first(raw, "expression"),
                negated=(raw.get("negated", "false").lower() == "true"),
                inputs=inputs,
            )
        )
    return elements


def parse_plcopen(path: Path) -> PLCProgram:
    source = Path(path)
    root = ET.parse(str(source)).getroot()
    pous: List[POU] = []
    for element in root.iter():
        if _local_name(element.tag) != "pou":
            continue
        name = element.get("name", "anonymous")
        pou_type = element.get("pouType", "unknown")
        variables = _parse_variables(element)
        body = _first_child_named(element, "body")
        if body is None:
            pous.append(POU(name=name, pou_type=pou_type, variables=variables, language="none"))
            continue
        st = _first_child_named(body, "ST")
        ld = _first_child_named(body, "LD")
        if st is not None:
            text = "\n".join(part for part in st.itertext())
            pous.append(
                POU(
                    name=name,
                    pou_type=pou_type,
                    variables=variables,
                    language="ST",
                    statements=parse_st(text),
                    raw_body=text,
                )
            )
        elif ld is not None:
            pous.append(
                POU(
                    name=name,
                    pou_type=pou_type,
                    variables=variables,
                    language="LD",
                    ld_elements=_parse_ld(ld),
                )
            )
        else:
            pous.append(POU(name=name, pou_type=pou_type, variables=variables, language="unknown"))
    return PLCProgram(source=source, pous=pous)

