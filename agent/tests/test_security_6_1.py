from src.security import scan_code

def test_scan_code_safe():
    code = "def next(self): pass"
    is_safe, errors = scan_code(code)
    assert is_safe
    assert not errors

def test_scan_code_forbidden_import():
    code = "import os\ndef next(self): pass"
    is_safe, errors = scan_code(code)
    assert not is_safe
    assert "forbidden_import: os" in errors

def test_scan_code_forbidden_call():
    code = "def next(self): eval('1 + 1')"
    is_safe, errors = scan_code(code)
    assert not is_safe
    assert "forbidden_call: eval" in errors

def test_scan_code_syntax_error():
    code = "def next(self) pass"
    is_safe, errors = scan_code(code)
    assert not is_safe
    assert any("syntax_error" in e for e in errors)
