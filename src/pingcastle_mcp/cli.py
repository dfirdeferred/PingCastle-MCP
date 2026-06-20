from __future__ import annotations
from getpass import getpass

from .config import save_url, Config
from .credentials import CredentialStore
from .enterprise_client import EnterpriseClient


def configure(input_fn=input, getpass_fn=getpass, store=None, validate=True) -> int:
    store = CredentialStore() if store is None else store
    url = input_fn("PingCastle Enterprise URL: ").strip().rstrip("/")
    key = getpass_fn("API key (hidden): ").strip()
    if not url or not key:
        print("URL and API key are both required.")
        return 1

    if validate:
        import asyncio

        async def _check():
            cfg = Config(enterprise_url=url, api_key=key, exe_path=None,
                         insecure_tls=True, login_location="pingcastle-mcp-configure")
            async with EnterpriseClient(cfg) as c:
                await c.login()
                await c.list_domains()

        try:
            asyncio.run(_check())
        except Exception as e:  # noqa: BLE001 — surface any validation failure
            print(f"Validation failed: {e}")
            return 2

    save_url(url)
    store.set_api_key(key)
    print("Saved. URL stored in config; API key stored in the OS keyring.")
    return 0
