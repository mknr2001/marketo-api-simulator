"""PHP-style serialization for FormFields values."""

from __future__ import annotations

from typing import Any


def php_serialize_string(value: str) -> str:
    """Serialize a string in PHP format: s:<byte-length>:"<value>";"""
    byte_length = len(value.encode("utf-8"))
    return f's:{byte_length}:"{value}";'


def php_serialize_int(value: int) -> str:
    """Serialize an integer in PHP format: i:<value>;"""
    return f"i:{value};"


def php_serialize_null() -> str:
    """Serialize a PHP null: N;"""
    return "N;"


def php_serialize_bool(value: bool) -> str:
    """Serialize a boolean in PHP format: b:1; or b:0;"""
    return f"b:{1 if value else 0};"


def php_serialize_value(value: Any) -> str:
    """Dispatch serialization based on Python type.

    Supports: str, int, bool (checked before int), None, list of tuples (array).
    """
    if value is None:
        return php_serialize_null()
    if isinstance(value, bool):
        return php_serialize_bool(value)
    if isinstance(value, int):
        return php_serialize_int(value)
    if isinstance(value, str):
        return php_serialize_string(value)
    if isinstance(value, list):
        # Treat list of (key, value) tuples as an associative array
        return php_serialize_array(value)
    raise TypeError(f"Unsupported type for PHP serialization: {type(value)}")


def php_serialize_array(pairs: list[tuple[str, Any]]) -> str:
    """Serialize an associative array in PHP format.

    Format: a:<pair-count>:{<key-serialization><value-serialization>...}

    Each key is serialized as a string, each value via php_serialize_value.
    """
    count = len(pairs)
    inner = ""
    for key, val in pairs:
        inner += php_serialize_string(key)
        inner += php_serialize_value(val)
    return f"a:{count}:{{{inner}}}"
