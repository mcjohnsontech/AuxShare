# backend/security/csrf.py
import os
import urllib.parse
from fastapi import Request, HTTPException, status
from typing import List, Set, Optional

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
# Session cookie name — kept in sync with security.session.SESSION_COOKIE_NAME
_SESSION_COOKIE_NAME = "aux_session"

class CSRFProtector:
    """
    CSRF Defense using Origin and Referer validation plus optional CSRF tokens.
    Protects state-changing endpoints when using browser session cookies.
    """
    def __init__(self, allowed_origins: Optional[List[str]] = None):
        if allowed_origins is None:
            allowed_origins = []
            
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
        allowed_origins.append(frontend_url)
        # Add loopback / localhost variants for local dev
        allowed_origins.extend([
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://localhost:3000",
            "http://127.0.0.1:3000"
        ])
        
        self.allowed_origins: Set[str] = set()
        for o in allowed_origins:
            parsed = urllib.parse.urlparse(o)
            if parsed.scheme and parsed.netloc:
                self.allowed_origins.add(f"{parsed.scheme}://{parsed.netloc}".lower())

    def is_origin_allowed(self, origin: str) -> bool:
        if not origin:
            return False
        parsed = urllib.parse.urlparse(origin.strip())
        norm = f"{parsed.scheme}://{parsed.netloc}".lower()
        return norm in self.allowed_origins

    def validate_request(self, request: Request) -> None:
        """Validate state-changing request against CSRF."""
        if request.method in SAFE_METHODS:
            return

        origin = request.headers.get("origin")
        referer = request.headers.get("referer")
        sec_fetch_site = request.headers.get("sec-fetch-site")

        # Browser explicitly flags cross-site requests
        if sec_fetch_site == "cross-site":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF Protection: Cross-site requests are rejected."
            )

        # Check Origin header
        if origin:
            if not self.is_origin_allowed(origin):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"CSRF Protection: Untrusted Origin '{origin}'."
                )
            return

        # Fallback to Referer header if Origin not set
        if referer:
            if not self.is_origin_allowed(referer):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"CSRF Protection: Untrusted Referer '{referer}'."
                )
            return

        # No Origin, no Referer.
        # CSRF is only exploitable when the browser automatically attaches session
        # cookies to a forged request.  A pure API call that carries no session
        # cookie is not a CSRF risk (the attacker can't steal or forge it).
        # Reject only when the session cookie is present — that is the signal
        # that a browser initiated this request and MUST have sent an Origin.
        if request.cookies.get(_SESSION_COOKIE_NAME):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "CSRF Protection: State-changing request carries a session cookie "
                    "but is missing both Origin and Referer headers."
                )
            )

default_csrf = CSRFProtector()
