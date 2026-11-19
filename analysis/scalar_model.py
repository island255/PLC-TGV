"""Single-scan fixed-width scalar execution."""
import re

from st_syntax import Program, names


WIDTHS = {'INT': 16, 'DINT': 32}


class Unsupported(ValueError):
    pass


class ScalarFault(ArithmeticError):
    pass


def wrap(value, kind):
    if kind == 'BOOL':
        if type(value) is not bool:
            raise Unsupported('Implicit numeric/Boolean conversion')
        return value
    if kind not in WIDTHS or type(value) is not int:
        raise Unsupported('Unsupported scalar value/type')
    width = WIDTHS[kind]
    return (value + (1 << (width-1))) % (1 << width) - (1 << (width-1))


def checked(value, kind):
    result = wrap(value, kind)
    if result != value:
        raise Unsupported('Value outside declared input/initializer range')
    return result


def infer(node, declarations):
    if node[0] == 'name':
        return declarations[node[1]]['type']
    if node[0] == 'constant':
        return 'BOOL' if type(node[1]) is bool else None
    if node[0] == 'unary':
        return 'BOOL' if node[1] in ('NOT','!') else infer(node[2], declarations)
    if node[1] in ('AND','&&','OR','||','XOR','=','==','<>','!=','<','<=','>','>='):
        return 'BOOL'
    a, b = infer(node[2], declarations), infer(node[3], declarations)
    if a and b and a != b:
        raise Unsupported('Mixed operand types')
    return a or b


def evaluate(node, env, declarations, hint=None):
    """Return an unboxed value; every arithmetic operator normalizes its width."""
    def numeric_kind(left, right, expected=None):
        a, b = infer(left, declarations), infer(right, declarations)
        if a and b and a != b:
            raise Unsupported('Mixed operand types')
        return a or b or (expected if expected in WIDTHS else 'DINT')

    def ev(n, expected=None):
        if n[0] == 'name':
            return env[n[1]], declarations[n[1]]['type']
        if n[0] == 'constant':
            k = 'BOOL' if type(n[1]) is bool else expected if expected in WIDTHS else 'DINT'
            return checked(n[1], k), k
        if n[0] == 'unary':
            if n[1] == '-' and n[2][0] == 'constant' and type(n[2][1]) is int:
                k = expected if expected in WIDTHS else 'DINT'
                return checked(-n[2][1], k), k
            value, k = ev(n[2], expected)
            if n[1] in ('NOT','!'):
                if k != 'BOOL': raise Unsupported('NOT requires BOOL in this profile')
                return not value, 'BOOL'
            if k not in WIDTHS: raise Unsupported('Unary minus requires integer')
            return wrap(-value, k), k
        op = n[1]
        if op in ('AND','&&','OR','||','XOR'):
            a, ka = ev(n[2]); b, kb = ev(n[3])
            if ka != 'BOOL' or kb != 'BOOL': raise Unsupported('Logical operands must be BOOL')
            return (a and b if op in ('AND','&&') else a or b if op in ('OR','||') else a != b), 'BOOL'
        k = numeric_kind(n[2], n[3], expected)
        a, ka = ev(n[2], k); b, kb = ev(n[3], k)
        if ka != kb: raise Unsupported('Mixed operand types')
        if op in ('=','==','<>','!=','<','<=','>','>='):
            if ka == 'BOOL' and op not in ('=','==','<>','!='):
                raise Unsupported('Ordered Boolean comparison')
            return {'=':a==b,'==':a==b,'<>':a!=b,'!=':a!=b,
                    '<':a<b,'<=':a<=b,'>':a>b,'>=':a>=b}[op], 'BOOL'
        if ka not in WIDTHS: raise Unsupported('Integer arithmetic requires integer operands')
        if op in ('/','MOD'):
            if b == 0: raise ScalarFault('division by zero')
            if a == -(1 << (WIDTHS[ka]-1)) and b == -1:
                raise ScalarFault('signed division overflow')
            quotient = (abs(a)//abs(b)) * (-1 if (a<0) != (b<0) else 1)
            return wrap(quotient if op == '/' else a-quotient*b, ka), ka
        if op not in ('+','-','*'): raise Unsupported('Unknown operator '+op)
        return wrap(a+b if op=='+' else a-b if op=='-' else a*b, ka), ka
    return ev(node, hint)[0]


def assignments(block):
    for s in block:
        if s[0] == 'assign': yield s
        else:
            for _, branch in s[1]: yield from assignments(branch)
            yield from assignments(s[2])


class TypedProgram(Program):
    def __init__(self, text):
        clean = re.sub(r'\(\*.*?\*\)|//[^\n]*', ' ', text, flags=re.S)
        if len(re.findall(r'\bEND_PROGRAM\b',clean,re.I)) != 1 or re.search(r'\bFUNCTION(?:_BLOCK)?\b',clean,re.I):
            raise Unsupported('Exactly one scalar program required')
        super().__init__(text)
        declarations = re.findall(r'\b(\w+)\s*(?:AT\s+%[IQM][XBWD]\d+(?:\.\d+)*\s*)?:\s*(?:BOOL|INT|DINT)\b',clean,re.I)
        if len(declarations) != len(self.declarations): raise Unsupported('Duplicate/incomplete declaration')
        addresses = re.findall(r'\bAT\s+(%[IQM][XBWD]\d+(?:\.\d+)*)',clean,re.I)
        if len(set(a.upper() for a in addresses)) != len(addresses): raise Unsupported('Address aliases')
        if any(not re.fullmatch(r'%[IQ]X\d+\.\d+',a,re.I) for a in addresses):
            raise Unsupported('Only distinct Boolean I/O bit addresses')
        for d in self.declarations.values():
            if d['type']=='BOOL' and d['initial'] is not None and d['initial'].upper() not in ('TRUE','FALSE'):
                raise Unsupported('Boolean initializer must be TRUE/FALSE')
        for s in assignments(self.statements):
            if self.declarations[s[1]]['input'] or not names(s[2]) <= set(self.declarations):
                raise Unsupported('Input assignment or undeclared variable')
        self.initial()

    def initial(self):
        env = super().initial()
        for n,d in self.declarations.items(): checked(env[n],d['type'])
        return env

    def evaluate(self, node, env, hint=None):
        return evaluate(node, env, self.declarations, hint)

    def step(self, state, inputs):
        expected = {n for n,d in self.declarations.items() if d['input']}
        if set(inputs) != expected: raise Unsupported('Input set does not match declaration')
        env = dict(state)
        for n,v in inputs.items(): env[n] = checked(v,self.declarations[n]['type'])
        def execute(block):
            for s in block:
                if s[0] == 'assign':
                    k = self.declarations[s[1]]['type']
                    env[s[1]] = wrap(self.evaluate(s[2],env,k),k)
                else:
                    for guard, branch in s[1]:
                        value = self.evaluate(guard,env)
                        if type(value) is not bool: raise Unsupported('IF guard must be BOOL')
                        if value:
                            execute(branch); break
                    else: execute(s[2])
        execute(self.statements)
        return env
