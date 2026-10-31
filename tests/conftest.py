# tests/conftest.py
import sys
import os
import pytest
from cryptography.fernet import Fernet

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)


# Establish test defaults before application imports load a developer's .env.
# Explicit settings inside individual tests still take precedence via monkeypatch.
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("COOKIE_SECURE", "false")
os.environ.setdefault("COOKIE_SAMESITE", "lax")

os.environ.setdefault("AUXSHARE_ENCRYPTION_KEYS", Fernet.generate_key().decode())


@pytest.fixture(autouse=True)
def offline_mapping_cache(monkeypatch):
    # Matching fixtures must not depend on an optional local Redis cache or
    # leave cache records behind while replaying recorded music catalogues.
    from cache.mapping_cache import MappingCache
    monkeypatch.setattr(MappingCache, "get", lambda *args, **kwargs: None)
    monkeypatch.setattr(MappingCache, "set_positive", lambda *args, **kwargs: None)
    monkeypatch.setattr(MappingCache, "set_negative", lambda *args, **kwargs: None)
