import time
import base64
import json
import httpx
import pytest
import respx

from pingcastle_mcp.config import Config
from pingcastle_mcp.enterprise_client import EnterpriseClient
from pingcastle_mcp.errors import AuthError, NetworkError


def make_token(exp_in=3600):
    payload = {"exp": int(time.time()) + exp_in, "nbf": int(time.time())}
    b = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    return f"Bearer header.{b}.sig"


def cfg():
    return Config(enterprise_url="https://pc.test", api_key="k",
                  exe_path=None, insecure_tls=True, login_location="test")


@respx.mock
async def test_login_returns_verbatim_bearer():
    token = make_token()
    respx.post("https://pc.test/api/Agent/Login").mock(
        return_value=httpx.Response(200, text=token))
    async with EnterpriseClient(cfg()) as c:
        header = await c.login()
    assert header == token
    assert header.startswith("Bearer ")


@respx.mock
async def test_login_failure_raises_auth_error():
    respx.post("https://pc.test/api/Agent/Login").mock(
        return_value=httpx.Response(400, text="bad key"))
    async with EnterpriseClient(cfg()) as c:
        with pytest.raises(AuthError):
            await c.login()


@respx.mock
async def test_get_refreshes_on_401_then_succeeds():
    login = respx.post("https://pc.test/api/Agent/Login").mock(
        return_value=httpx.Response(200, text=make_token()))
    route = respx.get("https://pc.test/api/Domains")
    route.side_effect = [httpx.Response(401), httpx.Response(200, json=[{"ok": 1}])]
    async with EnterpriseClient(cfg()) as c:
        data = await c._get("/api/Domains")
    assert data == [{"ok": 1}]
    assert login.call_count == 2  # initial + refresh after 401


@respx.mock
async def test_proactive_refresh_before_expiry():
    # token issued already inside the 60s skew window -> client re-logs in before the GET
    login = respx.post("https://pc.test/api/Agent/Login").mock(
        return_value=httpx.Response(200, text=make_token(exp_in=30)))
    respx.get("https://pc.test/api/Domains").mock(
        return_value=httpx.Response(200, json=[]))
    async with EnterpriseClient(cfg()) as c:
        await c.login()                # call 1; token already within skew
        await c._get("/api/Domains")   # _auth_header sees it expired -> call 2
    assert login.call_count == 2


@respx.mock
async def test_login_network_failure_raises_network_error():
    respx.post("https://pc.test/api/Agent/Login").mock(
        side_effect=httpx.ConnectError("boom"))
    async with EnterpriseClient(cfg()) as c:
        with pytest.raises(NetworkError):
            await c.login()


@respx.mock
async def test_login_adds_bearer_prefix_when_missing():
    respx.post("https://pc.test/api/Agent/Login").mock(
        return_value=httpx.Response(200, text="rawtoken.payload.sig"))
    async with EnterpriseClient(cfg()) as c:
        header = await c.login()
    assert header == "Bearer rawtoken.payload.sig"


@respx.mock
async def test_list_domains_parses(fixtures_dir):
    import json as _json
    domains = _json.loads((fixtures_dir / "domains.json").read_text())
    respx.post("https://pc.test/api/Agent/Login").mock(
        return_value=httpx.Response(200, text=make_token()))
    respx.get("https://pc.test/api/Domains").mock(
        return_value=httpx.Response(200, json=domains))
    async with EnterpriseClient(cfg()) as c:
        result = await c.list_domains()
    assert result[0].name == "cloud.lab"


@respx.mock
async def test_get_report_returns_dict(fixtures_dir):
    import json as _json
    report = _json.loads((fixtures_dir / "report_full.json").read_text())
    respx.post("https://pc.test/api/Agent/Login").mock(
        return_value=httpx.Response(200, text=make_token()))
    respx.get("https://pc.test/api/Reports/1002").mock(
        return_value=httpx.Response(200, json=report))
    async with EnterpriseClient(cfg()) as c:
        result = await c.get_report(1002)
    assert "riskRules" in result


@respx.mock
async def test_list_reports_parses(fixtures_dir):
    import json as _json
    from pingcastle_mcp.models import ReportListItem
    reports = _json.loads((fixtures_dir / "reports_list.json").read_text())
    respx.post("https://pc.test/api/Agent/Login").mock(
        return_value=httpx.Response(200, text=make_token()))
    respx.get("https://pc.test/api/Domains/1/Reports").mock(
        return_value=httpx.Response(200, json=reports))
    async with EnterpriseClient(cfg()) as c:
        result = await c.list_reports(1)
    assert isinstance(result[0], ReportListItem)
    assert result[0].id == reports[0]["id"]


@respx.mock
async def test_get_latest_report_returns_dict(fixtures_dir):
    import json as _json
    report = _json.loads((fixtures_dir / "report_full.json").read_text())
    respx.post("https://pc.test/api/Agent/Login").mock(
        return_value=httpx.Response(200, text=make_token()))
    respx.get("https://pc.test/api/Domains/1/LatestReport").mock(
        return_value=httpx.Response(200, json=report))
    async with EnterpriseClient(cfg()) as c:
        result = await c.get_latest_report(1)
    assert isinstance(result, dict)
    assert "riskRules" in result
