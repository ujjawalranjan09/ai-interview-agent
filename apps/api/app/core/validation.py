import re
import uuid as uuid_lib

_html_tags = re.compile(r"<[^>]+>")


def sanitize_string(value: str) -> str:
    value = _html_tags.sub("", value)
    value = value.strip()
    return value[:10000]


def validate_uuid(value: str) -> uuid_lib.UUID:
    return uuid_lib.UUID(value)


def validate_email(value: str) -> str:
    return value.strip().lower()
