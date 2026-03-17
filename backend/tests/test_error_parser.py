from app.services.error_parser import parse_execution_error


def test_parse_name_error_traceback_into_structured_message():
    error = parse_execution_error(
        """
Traceback (most recent call last):
  File "/sandbox/workdir/strategy.py", line 15, in <module>
    signal = sma_period + 1
NameError: name 'sma_period' is not defined
""".strip()
    )

    assert error["type"] == "NameError"
    assert error["line"] == 15
    assert "sma_period" in error["message"]
    assert "变量" in error["suggestion"]
    assert "ctx.params" in error["example_code"]


def test_parse_import_error_sanitizes_internal_paths():
    error = parse_execution_error(
        """
Traceback (most recent call last):
  File "/home/user/project/src/strategy.py", line 3, in <module>
    import talibx
ModuleNotFoundError: No module named 'talibx'
""".strip()
    )

    assert error["type"] == "ImportError"
    assert error["line"] == 3
    assert "talibx" in error["message"]
    assert "/home/user" not in error["raw_error"]
    assert "支持的依赖库" in error["suggestion"]


def test_parse_syntax_error_uses_readable_message():
    error = parse_execution_error(
        """
  File "/tmp/strategy.py", line 8
    if price > 0
                ^
SyntaxError: expected ':'
""".strip()
    )

    assert error["type"] == "SyntaxError"
    assert error["line"] == 8
    assert "第 8 行" in error["message"]
    assert "expected" in error["message"]

