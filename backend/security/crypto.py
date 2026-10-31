# backend/security/crypto.py
import os
import base64
from typing import List, Optional
from cryptography.fernet import Fernet, MultiFernet, InvalidToken

class TokenCrypto:
    """
    Symmetric encryption service for OAuth tokens using Fernet / MultiFernet.
    Supports seamless key rotation: the first key in the list is used for
    encryption, while all configured keys can decrypt.
    """
    def __init__(self, keys: Optional[List[str]] = None):
        if not keys:
            keys = self._load_or_generate_keys()
        self.keys = keys
        self.fernets = [Fernet(k.encode() if isinstance(k, str) else k) for k in self.keys]
        self.multi_fernet = MultiFernet(self.fernets)

    def _load_or_generate_keys(self) -> List[str]:
        # 1. Check environment variable (comma-separated)
        env_keys = os.getenv("AUXSHARE_ENCRYPTION_KEYS") or os.getenv("ENCRYPTION_KEYS")
        if env_keys:
            return [k.strip() for k in env_keys.split(",") if k.strip()]

        # 2. Check single secret key
        single_key = os.getenv("AUXSHARE_SECRET_KEY")
        if single_key and len(single_key) == 44:
            return [single_key.strip()]

        # 3. Production guard: fail loudly if no key is configured
        environment = os.getenv("AUXSHARE_ENV", os.getenv("ENVIRONMENT", "development")).lower()
        if environment == "production":
            raise RuntimeError(
                "AUXSHARE_ENCRYPTION_KEYS must be set in production. "
                "Generate a key with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )

        # 4. Development fallback: persist to a local hidden secret file
        secret_file = os.path.join(os.path.dirname(__file__), "..", ".secret_encryption_key")
        if os.path.exists(secret_file):
            with open(secret_file, "r", encoding="utf-8") as f:
                saved_key = f.read().strip()
                if saved_key:
                    return [saved_key]

        new_key = Fernet.generate_key().decode()
        try:
            with open(secret_file, "w", encoding="utf-8") as f:
                f.write(new_key)
        except OSError:
            pass
        return [new_key]

    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext string into base64 ciphertext."""
        if not plaintext:
            return ""
        return self.multi_fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt base64 ciphertext back to plaintext."""
        if not ciphertext:
            return ""
        try:
            return self.multi_fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
        except InvalidToken:
            raise ValueError("Decryption failed: invalid token or mismatched encryption key.")

    def rotate(self, ciphertext: str) -> str:
        """Re-encrypt ciphertext with the latest key."""
        if not ciphertext:
            return ""
        return self.multi_fernet.rotate(ciphertext.encode("utf-8")).decode("utf-8")

# Default global instance
default_crypto = TokenCrypto()

