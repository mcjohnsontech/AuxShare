# backend/security/redaction.py
import re
import logging
from typing import Any, Dict

# Regex patterns for sensitive tokens and authorization headers
BEARER_TOKEN_PATTERN = re.compile(r'(?i)(bearer\s+)([a-zA-Z0-9_\-\.]{15,})')
SPOTIFY_TOKEN_PATTERN = re.compile(r'(?i)(access_token["\':\s=]+)([a-zA-Z0-9_\-\.]{20,})')
REFRESH_TOKEN_PATTERN = re.compile(r'(?i)(refresh_token["\':\s=]+)([a-zA-Z0-9_\-\.]{20,})')
AUTH_HEADER_PATTERN = re.compile(r'(?i)(["\']?authorization["\']?\s*[:=]\s*["\']?)([^"\'\n\r]+)(["\']?)')
SECRET_PARAM_PATTERN = re.compile(r'(?i)(client_secret["\':\s=]+)([a-zA-Z0-9_\-\.]{10,})')

def redact_sensitive_string(text: str) -> str:
    """Mask tokens and sensitive authorization credentials in text."""
    if not isinstance(text, str):
        return text
    
    redacted = BEARER_TOKEN_PATTERN.sub(r'\1[REDACTED_TOKEN]', text)
    redacted = SPOTIFY_TOKEN_PATTERN.sub(r'\1[REDACTED_TOKEN]', redacted)
    redacted = REFRESH_TOKEN_PATTERN.sub(r'\1[REDACTED_TOKEN]', redacted)
    redacted = SECRET_PARAM_PATTERN.sub(r'\1[REDACTED_SECRET]', redacted)
    redacted = AUTH_HEADER_PATTERN.sub(r'\1[REDACTED_AUTH]\3', redacted)
    return redacted

def redact_sensitive_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively scrub sensitive keys from dictionaries."""
    sanitized = {}
    sensitive_keys = {
        "access_token", "refresh_token", "token", "authorization", 
        "client_secret", "secret", "password"
    }
    for k, v in data.items():
        if k.lower() in sensitive_keys and isinstance(v, str):
            sanitized[k] = "[REDACTED]"
        elif isinstance(v, dict):
            sanitized[k] = redact_sensitive_dict(v)
        elif isinstance(v, list):
            sanitized[k] = [
                redact_sensitive_dict(item) if isinstance(item, dict)
                else (redact_sensitive_string(item) if isinstance(item, str) else item)
                for item in v
            ]
        elif isinstance(v, str):
            sanitized[k] = redact_sensitive_string(v)
        else:
            sanitized[k] = v
    return sanitized

class SensitiveDataLogFilter(logging.Filter):
    """Logging filter that ensures sensitive tokens and auth headers are never logged."""
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_sensitive_string(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = redact_sensitive_dict(record.args)
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    redact_sensitive_string(arg) if isinstance(arg, str) else arg
                    for arg in record.args
                )
        return True

