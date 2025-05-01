from src.utils import validate_nickname, sanitize_text

def test_validate_nickname_ok():
    assert validate_nickname("Pepito_99") is True

def test_validate_nickname_bad():
    assert validate_nickname("   ") is False

def test_sanitize_removes_html():
    assert sanitize_text("<b>Hola</b>") == "Hola"
