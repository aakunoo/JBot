from src.utils.validators import validate_nickname
from src.utils.input_sanitizer import sanitize_text

def test_validate_nickname_ok():
    assert validate_nickname("Pepito_99") is True

def test_validate_nickname_bad():
    assert validate_nickname("   ") is True

def test_sanitize_removes_html():
    assert sanitize_text("<b>Hola</b>") == "bHolab"
