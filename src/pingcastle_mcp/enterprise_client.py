from __future__ import annotations
import base64
import json
import time
from typing import Any

import httpx

from .config import Config
from .errors import AuthError, NetworkError, NotFoundError
from .models import Domain, ReportListItem, parse_domain, parse_report_list_item

_REFRESH_SKEW = 60  # refresh this many seconds before exp


def _decode_exp(header_value: str) -> int | None:
    try:
        token = header_value.removeprefix("Bearer ").strip()
        payload_b64 = token.split(".")[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return int(payload.get("exp")) if "exp" in payload else None
    except Exception:
        return None


class EnterpriseClient:
    def __init__(self, config: Config):
        self._cfg = config
        self._auth: str | None = None
        self._exp: int | None = None
        self._client = httpx.AsyncClient(
            base_url=config.enterprise_url,
            verify=not config.insecure_tls,
            timeout=30.0,
        )

    async def __aenter__(self) -> "EnterpriseClient":
        return self

    async def __aexit__(self, *exc) -> None:
        await self._client.aclose()

    def _token_expired(self) -> bool:
        if self._auth is None:
            return True
        if self._exp is None:
            return False
        return time.time() >= (self._exp - _REFRESH_SKEW)

    async def login(self) -> str:
        body = {"apikey": self._cfg.api_key, "location": self._cfg.login_location}
        try:
            resp = await self._client.post("/api/Agent/Login", json=body)
        except httpx.HTTPError as e:
            raise NetworkError(f"Cannot reach {self._cfg.enterprise_url}: {e}") from e
        if resp.status_code != 200:
            raise AuthError(f"Login failed ({resp.status_code}). Check the API key.")
        header = resp.text.strip()
        if not header.startswith("Bearer "):
            header = f"Bearer {header}"
        self._auth = header
        self._exp = _decode_exp(header)
        return header

    async def _auth_header(self) -> str:
        if self._token_expired():
            await self.login()
        return self._auth  # type: ignore[return-value]

    async def _get(self, path: str, params: dict | None = None) -> Any:
        header = await self._auth_header()
        try:
            resp = await self._client.get(path, params=params,
                                          headers={"Authorization": header})
            if resp.status_code == 401:
                header = await self.login()
                resp = await self._client.get(
                    path, params=params,
                    headers={"Authorization": header})
        except httpx.HTTPError as e:
            raise NetworkError(f"Request to {path} failed: {e}") from e
        if resp.status_code == 404:
            raise NotFoundError(f"Not found: {path}")
        if resp.status_code == 401:
            raise AuthError("Unauthorized after refresh — check API key/permissions.")
        resp.raise_for_status()
        return resp.json()

    async def list_domains(self) -> list[Domain]:
        data = await self._get("/api/Domains")
        return [parse_domain(d) for d in data]

    async def list_reports(self, domain_id: int) -> list[ReportListItem]:
        data = await self._get(f"/api/Domains/{domain_id}/Reports")
        return [parse_report_list_item(d) for d in data]

    async def get_report(self, report_id: int) -> dict:
        return await self._get(f"/api/Reports/{report_id}")

    async def get_latest_report(self, domain_id: int) -> dict:
        return await self._get(f"/api/Domains/{domain_id}/LatestReport")
