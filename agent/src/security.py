import ast
from typing import List, Tuple

FORBIDDEN_IMPORTS = {"os", "sys", "subprocess", "socket", "requests", "ctypes", "importlib", "shutil", "urllib", "builtins"}
FORBIDDEN_CALLS = {"eval", "exec", "open", "compile", "globals", "locals", "__import__"}

class SecurityScanner(ast.NodeVisitor):
    def __init__(self):
        self.errors = []
        
    def visit_Import(self, node: ast.Import):
        for name in node.names:
            if name.name.split('.')[0] in FORBIDDEN_IMPORTS:
                self.errors.append(f"forbidden_import: {name.name}")
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module and node.module.split('.')[0] in FORBIDDEN_IMPORTS:
            self.errors.append(f"forbidden_import: {node.module}")
        for name in node.names:
            if name.name.split('.')[0] in FORBIDDEN_IMPORTS:
                self.errors.append(f"forbidden_import: {name.name}")
        self.generic_visit(node)
        
    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
            self.errors.append(f"forbidden_call: {node.func.id}")
        elif isinstance(node.func, ast.Attribute) and node.func.attr in FORBIDDEN_CALLS:
            self.errors.append(f"forbidden_call: {node.func.attr}")
        self.generic_visit(node)

def scan_code(code: str) -> Tuple[bool, List[str]]:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, [f"syntax_error: {e.lineno}:{e.offset} {e.msg}"]
        
    scanner = SecurityScanner()
    scanner.visit(tree)
    
    if scanner.errors:
        return False, scanner.errors
    return True, []
