# backend/security/oauth.py
import secrets
import hashlib
import base64
import re

def generate_code_verifier(length: int = 64) -> str:
    """
    Generate an RFC 7636 compliant PKCE code verifier.
    Must be between 43 and 128 characters using unreserved URL characters.
    """
    if length < 43 or length > 128:
        raise ValueError("PKCE code verifier length must be between 43 and 128 characters.")
    # token_urlsafe uses [A-Za-z0-9-_]
    # token_urlsafe(nbytes) generates ~4/3 * nbytes characters
    token = secrets.token_urlsafe(length)[:length]
    # Ensure minimum 43 chars
    while len(token) < length:
        token += secrets.token_urlsafe(16)
    return token[:length]

def generate_code_challenge(verifier: str) -> str:
    """
    Generate an RFC 7636 code challenge from a verifier using S256:
    code_challenge = BASE64URL-ENCODE(SHA256(ASCII(code_verifier)))
    without padding '='.
    """
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return challenge

def validate_pkce_challenge(verifier: str, challenge: str) -> bool:
    """Validate that a code verifier matches a code challenge."""
    if not verifier or not challenge:
        return False
    computed = generate_code_challenge(verifier)
    return secrets.compare_digest(computed, challenge)

def generate_state(nbytes: int = 32) -> str:
    """Generate a high-entropy OAuth state parameter for CSRF mitigation."""
    return secrets.token_urlsafe(nbytes)

