from __future__ import annotations

import re
from typing import Iterable, List, Optional, Sequence, Set, Tuple

from .model import Statement


Token = Tuple[str, str, int]


_BLOCK_PATTERNS = [
    ("ELSIF", re.compile(r"^ELSIF\b(.*?)\bTHEN\b", re.IGNORECASE)),
    ("IF", re.compile(r"^IF\b(.*?)\bTHEN\b", re.IGNORECASE)),
    ("WHILE", re.compile(r"^WHILE\b(.*?)\bDO\b", re.IGNORECASE)),
    ("END_IF", re.compile(r"^END_?IF\b\s*;?", re.IGNORECASE)),
    ("END_WHILE", re.compile(r"^END_?WHILE\b\s*;?", re.IGNORECASE)),
    ("ELSE", re.compile(r"^ELSE\b\s*;?", re.IGNORECASE)),
    ("TRY", re.compile(r"^__TRY\b\s*;?", re.IGNORECASE)),
    ("CATCH", re.compile(r"^__CATCH\s*(?:\((.*?)\))?\s*;?", re.IGNORECASE)),
    ("END_TRY", re.compile(r"^__ENDTRY\b\s*;?", re.IGNORECASE)),
]


def tokenize_st(text: str) -> List[Token]:
    text = re.sub(r"\(\*.*?\*\)", " ", text, flags=re.DOTALL)
    tokens: List[Token] = []
    for line_number, original in enumerate(text.replace("\r", "").split("\n"), 1):
        line = re.sub(r"//.*$", "", original).strip()
        while line:
            matched = False
            for kind, pattern in _BLOCK_PATTERNS:
                match = pattern.match(line)
                if not match:
                    continue
                payload = ""
                if kind in {"IF", "ELSIF", "WHILE"}:
                    payload = (match.group(1) or "").strip()
                elif kind == "CATCH":
                    payload = (match.group(1) or "exception").strip()
                tokens.append((kind, payload, line_number))
                line = line[match.end():].strip()
                matched = True
                break
            if matched:
                continue

            semicolon = line.find(";")
            if semicolon >= 0:
                chunk = line[:semicolon].strip()
                line = line[semicolon + 1:].strip()
            else:
                chunk = line.strip()
                line = ""
            if chunk:
                tokens.append(("SIMPLE", chunk, line_number))
    return tokens


def _simple_statement(text: str, line: int) -> Statement:
    assignment = re.match(r"^([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)?)\s*:\s*=\s*(.+)$", text, re.DOTALL)
    if assignment:
        return Statement(
            kind="assignment",
            text=text,
            line=line,
            lhs=assignment.group(1).strip(),
            rhs=assignment.group(2).strip(),
        )
    call = re.match(r"^([A-Za-z_]\w*)\s*\((.*)\)$", text, re.DOTALL)
    if call:
        return Statement(kind="call", text=text, line=line, callee=call.group(1), condition=call.group(2).strip())
    return Statement(kind="raw", text=text, line=line)


def _parse_sequence(tokens: Sequence[Token], index: int, stops: Set[str]) -> Tuple[List[Statement], int]:
    statements: List[Statement] = []
    while index < len(tokens):
        kind, payload, line = tokens[index]
        if kind in stops:
            break
        if kind == "SIMPLE":
            statements.append(_simple_statement(payload, line))
            index += 1
            continue
        if kind == "IF":
            branches: List[Tuple[str, List[Statement]]] = []
            condition = payload
            index += 1
            body, index = _parse_sequence(tokens, index, {"ELSIF", "ELSE", "END_IF"})
            branches.append((condition, body))
            while index < len(tokens) and tokens[index][0] == "ELSIF":
                condition = tokens[index][1]
                index += 1
                body, index = _parse_sequence(tokens, index, {"ELSIF", "ELSE", "END_IF"})
                branches.append((condition, body))
            if index < len(tokens) and tokens[index][0] == "ELSE":
                index += 1
                body, index = _parse_sequence(tokens, index, {"END_IF"})
                branches.append(("ELSE", body))
            if index < len(tokens) and tokens[index][0] == "END_IF":
                index += 1
            statements.append(Statement(kind="if", text="IF", line=line, condition=payload, branches=branches))
            continue
        if kind == "WHILE":
            index += 1
            body, index = _parse_sequence(tokens, index, {"END_WHILE"})
            if index < len(tokens) and tokens[index][0] == "END_WHILE":
                index += 1
            statements.append(Statement(kind="while", text="WHILE " + payload, line=line, condition=payload, children=body))
            continue
        if kind == "TRY":
            index += 1
            normal, index = _parse_sequence(tokens, index, {"CATCH", "END_TRY"})
            branches = [("no_error", normal)]
            if index < len(tokens) and tokens[index][0] == "CATCH":
                exception_name = tokens[index][1] or "exception"
                index += 1
                caught, index = _parse_sequence(tokens, index, {"END_TRY"})
                branches.append(("error(" + exception_name + ")", caught))
            if index < len(tokens) and tokens[index][0] == "END_TRY":
                index += 1
            statements.append(Statement(kind="try", text="__TRY", line=line, branches=branches))
            continue

        statements.append(Statement(kind="raw", text=kind + (" " + payload if payload else ""), line=line))
        index += 1
    return statements, index


def parse_st(text: str) -> List[Statement]:
    statements, _ = _parse_sequence(tokenize_st(text), 0, set())
    return statements


def walk_statements(statements: Iterable[Statement]) -> Iterable[Statement]:
    for statement in statements:
        yield statement
        for child in walk_statements(statement.children):
            yield child
        for _, branch in statement.branches:
            for child in walk_statements(branch):
                yield child


_COMPARISON = re.compile(
    r"([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)?|[-+]?\d+(?:\.\d+)?)\s*"
    r"(<=|>=|<>|(?<!:)=(?!=)|<|>)\s*"
    r"([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)?|[-+]?\d+(?:\.\d+)?)",
    re.IGNORECASE,
)


def comparisons(expression: str) -> List[Tuple[str, str, str]]:
    return [(m.group(1), m.group(2), m.group(3)) for m in _COMPARISON.finditer(expression or "")]


def identifiers(expression: str) -> Set[str]:
    ignored = {"IF", "THEN", "AND", "OR", "NOT", "TRUE", "FALSE", "DO"}
    return {
        token
        for token in re.findall(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)?", expression or "")
        if token.upper() not in ignored
    }

