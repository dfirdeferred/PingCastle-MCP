from __future__ import annotations

SERVICE = "pingcastle-mcp"
USERNAME = "api_key"


class CredentialStore:
    """Stores the API key in the OS keyring."""

    def __init__(self, keyring_backend=None):
        if keyring_backend is None:
            import keyring
            keyring_backend = keyring
        self._kr = keyring_backend

    def get_api_key(self) -> str | None:
        return self._kr.get_password(SERVICE, USERNAME)

    def set_api_key(self, key: str) -> None:
        self._kr.set_password(SERVICE, USERNAME, key)

    def delete_api_key(self) -> None:
        self._kr.delete_password(SERVICE, USERNAME)
