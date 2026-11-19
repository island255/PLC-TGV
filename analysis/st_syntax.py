"""Parser for the supported scalar ST subset and safety requirements."""
import itertools
import re


TOKEN = re.compile(r"\s*(?:(:=|<=|>=|<>|==|!=|&&|\|\||[();:+*/<>=!\-])|([A-Za-z_]\w*)|(\d+))")


PRECEDENCE = {"OR": 1, "||": 1, "XOR": 2, "AND": 3, "&&": 3,
              "=": 4, "==": 4, "<>": 4, "!=": 4, "<": 4, "<=": 4, ">": 4, ">=": 4,
              "+": 5, "-": 5, "*": 6, "/": 6, "MOD": 6}


def tokens(text):
    out = []
    offset = 0
    while offset < len(text):
        if not text[offset:].strip():
            break
        match = TOKEN.match(text, offset)
        if not match:
            raise ValueError("Unsupported source token near " + text[offset:offset+60])
        out.append(next(v for v in match.groups() if v is not None))
        offset = match.end()
    return out


class Expression:
    def __init__(self, items):
        self.items = items
        self.position = 0

    def parse(self, minimum=0):
        if self.position >= len(self.items):
            raise ValueError("Missing expression")
        value = self.items[self.position]
        self.position += 1
        if value.upper() in ("NOT", "!") or value == "-":
            left = ("unary", value.upper(), self.parse(7))
        elif value == "(":
            left = self.parse()
            if self.items[self.position] != ")":
                raise ValueError("Missing closing parenthesis")
            self.position += 1
        elif value.upper() in ("TRUE", "FALSE"):
            left = ("constant", value.upper() == "TRUE")
        elif value.isdigit():
            left = ("constant", int(value))
        else:
            left = ("name", value.casefold())
        while self.position < len(self.items):
            op = self.items[self.position].upper()
            precedence = PRECEDENCE.get(op, -1)
            if precedence < minimum:
                break
            self.position += 1
            right = self.parse(precedence + 1)
            left = ("binary", op, left, right)
        return left


def expression(text):
    parser = Expression(tokens(text))
    node = parser.parse()
    if parser.position != len(parser.items):
        raise ValueError("Unconsumed expression tokens")
    return node


class Program:
    def __init__(self, text):
        clean = re.sub(r"\(\*.*?\*\)", "", text, flags=re.S)
        clean = re.sub(r"//[^\n]*", "", clean)
        match = re.search(r"\bPROGRAM\s+\w+\b(.*?)\bEND_PROGRAM\b", clean, re.I | re.S)
        if not match:
            raise ValueError("One scalar program required")
        content = match[1]
        self.declarations = {}
        while True:
            block = re.match(r"\s*(VAR(?:_INPUT|_OUTPUT)?)\b(.*?)\bEND_VAR\b", content, re.I | re.S)
            if not block:
                break
            for declaration in block[2].split(";"):
                if not declaration.strip():
                    continue
                d = re.fullmatch(r"\s*(\w+)(?:\s+AT\s+(%[IQM][XBWD]\d+(?:\.\d+)*))?\s*:\s*(BOOL|INT|DINT)(?:\s*:=\s*(TRUE|FALSE|-?\d+))?\s*", declaration, re.I)
                if not d:
                    raise ValueError("Unsupported declaration " + declaration)
                name, address, kind, initial = d.groups()
                self.declarations[name.casefold()] = {
                    "type": kind.upper(), "initial": initial,
                    "input": block[1].upper() == "VAR_INPUT" or bool(address and address.upper().startswith("%I"))}
            content = content[block.end():]
        self.body_text = content
        self.items = tokens(content)
        self.pos = 0
        self.statements = self.block(set())
        if self.pos != len(self.items):
            raise ValueError("Unconsumed program tokens")

    def until(self, terminator):
        start = self.pos
        while self.pos < len(self.items) and self.items[self.pos].upper() != terminator:
            self.pos += 1
        if self.pos >= len(self.items):
            raise ValueError("Missing " + terminator)
        parser = Expression(self.items[start:self.pos])
        node = parser.parse()
        if parser.position != len(parser.items):
            raise ValueError("Unconsumed statement expression")
        self.pos += 1
        return node

    def block(self, stops):
        statements = []
        while self.pos < len(self.items) and self.items[self.pos].upper() not in stops:
            token = self.items[self.pos]
            self.pos += 1
            if token == ";":
                continue
            if token.upper() == "IF":
                branches = []
                condition = self.until("THEN")
                branches.append((condition, self.block({"ELSIF", "ELSE", "END_IF"})))
                while self.items[self.pos].upper() == "ELSIF":
                    self.pos += 1
                    condition = self.until("THEN")
                    branches.append((condition, self.block({"ELSIF", "ELSE", "END_IF"})))
                default = []
                if self.items[self.pos].upper() == "ELSE":
                    self.pos += 1
                    default = self.block({"END_IF"})
                if self.items[self.pos].upper() != "END_IF":
                    raise ValueError("Missing END_IF")
                self.pos += 1
                statements.append(("if", branches, default))
            else:
                name = token.casefold()
                if self.items[self.pos] != ":=" or name not in self.declarations:
                    raise ValueError("Unsupported statement " + token)
                self.pos += 1
                statements.append(("assign", name, self.until(";")))
        return statements

    def initial(self):
        env = {}
        for name, d in self.declarations.items():
            raw = d["initial"]
            env[name] = (raw.upper() == "TRUE" if raw else False) if d["type"] == "BOOL" else int(raw or "0")
        return env


def properties_ast(properties):
    out = []
    for prop in properties:
        if prop["kind"] == "reachability":
            continue
        if prop["kind"] == "invariant":
            out.append(expression(prop["expression"]))
        elif prop["kind"] == "mutual_exclusion":
            out += [expression("!(" + a + " && " + b + ")")
                    for a, b in itertools.combinations(prop["variables"], 2)]
        else:
            raise ValueError("Unsupported property")
    return out


def names(node):
    if node[0] == "name":
        return {node[1]}
    if node[0] == "constant":
        return set()
    if node[0] == "unary":
        return names(node[2])
    return names(node[2]) | names(node[3])
