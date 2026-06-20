from __future__ import annotations
import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Mapping

from .credentials import CredentialStore
from .errors import ConfigError


def _config_dir() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "pingcastle-mcp"


CONFIG_PATH = _config_dir() / "config.toml"


@dataclass
class Config:
    enterprise_url: str
    api_key: str
    exe_path: str | None
    insecure_tls: bool
    login_location: str


def save_url(url: str) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    escaped = url.replace("\\", "\\\\").replace('"', '\\"')
    # Only a single non-secret key; write minimal TOML directly.
    CONFIG_PATH.write_text(f'enterprise_url = "{escaped}"\n', encoding="utf-8")


def read_saved_url() -> str | None:
    if not CONFIG_PATH.exists():
        return None
    data = tomllib.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return data.get("enterprise_url")


def _truthy(v: str | None) -> bool:
    return str(v).lower() in {"1", "true", "yes"} if v is not None else False


def load_config(env: Mapping | None = None, store: CredentialStore | None = None) -> Config:
    env = os.environ if env is None else env
    store = CredentialStore() if store is None else store

    url = env.get("PINGCASTLE_ENTERPRISE_URL") or read_saved_url()
    if not url:
        raise ConfigError(
            "No Enterprise URL configured. Run `pingcastle-mcp configure` "
            "or set PINGCASTLE_ENTERPRISE_URL."
        )

    key = env.get("PINGCASTLE_API_KEY") or store.get_api_key()
    if not key:
        raise ConfigError(
            "No API key configured. Run `pingcastle-mcp configure` "
            "or set PINGCASTLE_API_KEY."
        )

    return Config(
        enterprise_url=url.rstrip("/"),
        api_key=key,
        exe_path=env.get("PINGCASTLE_EXE_PATH"),
        insecure_tls=_truthy(env.get("PINGCASTLE_INSECURE_TLS")),
        login_location=env.get("PINGCASTLE_LOGIN_LOCATION", "pingcastle-mcp"),
    )
