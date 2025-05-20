import re
import ast

def load_code_file(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def validate_ast(code):
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False

def scan_for_dangerous_patterns(code):
    flags = []
    patterns = {
        "Hardcoded API key": r"api[_-]?key\s*=\s*['\"](.+?)['\"]",
        "Hardcoded password": r"pass(word)?\s*=\s*['\"](.+?)['\"]",
        "Hardcoded secret": r"secret\s*=\s*['\"](.+?)['\"]",
        "os.system usage": r"os\.system\(",
        "eval usage": r"\beval\(",
        "exec usage": r"\bexec\(",
        "token in code": r"token\s*=\s*['\"](.+?)['\"]"
    }
    for label, pattern in patterns.items():
        if re.search(pattern, code, re.IGNORECASE | re.MULTILINE):
            flags.append(label)
    return flags, patterns

def redact_code(code, patterns):
    for pattern in patterns.values():
        code = re.sub(pattern, "[REDACTED]", code, flags=re.IGNORECASE | re.MULTILINE)
    return code

class ObfuscatedStringDetector(ast.NodeVisitor):
    def __init__(self):
        self.suspicious = []

    def visit_Assign(self, node):
        if isinstance(node.value, ast.BinOp) and isinstance(node.value.op, ast.Add):
            if isinstance(node.value.left, ast.Str) and isinstance(node.value.right, ast.Str):
                self.suspicious.append("String literal concatenation in assignment")
        elif isinstance(node.value, ast.Call):
            func = node.value.func
            if isinstance(func, ast.Attribute) and func.attr == 'join':
                if isinstance(func.value, ast.Str) and isinstance(node.value.args[0], (ast.List, ast.Tuple)):
                    if all(isinstance(el, ast.Str) for el in node.value.args[0].elts):
                        self.suspicious.append("String join from literals in assignment")
        self.generic_visit(node)

def detect_obfuscated_strings(code):
    try:
        tree = ast.parse(code)
        detector = ObfuscatedStringDetector()
        detector.visit(tree)
        return detector.suspicious
    except Exception:
        return []