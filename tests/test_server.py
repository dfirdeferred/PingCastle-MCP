import json
import pytest
from pingcastle_mcp.config import Config
from pingcastle_mcp import server as server_mod


def cfg():
    return Config(enterprise_url="https://pc.test", api_key="k",
                  exe_path=None, insecure_tls=True, login_location="t")


class StubClient:
    def __init__(self, report):
        self._report = report

    async def __aenter__(self): return self
    async def __aexit__(self, *a): return None

    async def get_report(self, rid): return self._report
    async def get_latest_report(self, did): return self._report


@pytest.fixture
def report(fixtures_dir):
    return json.loads((fixtures_dir / "report_full.json").read_text())


async def test_get_report_summary_tool(report, monkeypatch):
    monkeypatch.setattr(server_mod, "EnterpriseClient", lambda c: StubClient(report))
    srv = server_mod.build_server(cfg())
    fn = srv._tool_for("get_report_summary")
    out = await fn(report_id=1002)
    assert out["domain_fqdn"] == "cloud.lab"
    assert out["top_findings"][0]["points"] >= out["top_findings"][-1]["points"]
    assert out["report_id"] == 1002
    assert isinstance(out["findings_by_category"], dict)


async def test_run_scan_unavailable_message(monkeypatch):
    monkeypatch.setattr(server_mod, "EnterpriseClient", lambda c: StubClient({}))
    srv = server_mod.build_server(cfg())  # exe_path None -> scanner unavailable
    fn = srv._tool_for("run_scan")
    out = await fn(server="cloud.lab")
    assert out["success"] is False
    assert "not available" in out["message"].lower()


async def test_compare_reports_tool_is_json_serializable(fixtures_dir, monkeypatch):
    cur = json.loads((fixtures_dir / "report_full.json").read_text())
    prev = json.loads((fixtures_dir / "report_full_prev.json").read_text())

    class TwoReportClient:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *a):
            return None
        async def get_report(self, rid):
            return cur if rid == 1002 else prev

    monkeypatch.setattr(server_mod, "EnterpriseClient", lambda c: TwoReportClient())
    srv = server_mod.build_server(cfg())
    fn = srv._tool_for("compare_reports")
    out = await fn(report_id_a=1002, report_id_b=1)
    # Proves the whole return value (score_deltas, new, resolved, unchanged) serializes
    json.dumps(out)
    assert "global" in out["score_deltas"]
    assert isinstance(out["unchanged"], list)
    assert len(out["new"]) == 9
    assert all(isinstance(f, dict) for f in out["new"])


async def test_get_findings_tool_filters_by_points(fixtures_dir, monkeypatch):
    report = json.loads((fixtures_dir / "report_full.json").read_text())

    class OneReportClient:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *a):
            return None
        async def get_report(self, rid):
            return report

    monkeypatch.setattr(server_mod, "EnterpriseClient", lambda c: OneReportClient())
    srv = server_mod.build_server(cfg())
    fn = srv._tool_for("get_findings")
    out = await fn(report_id=1002, min_points=20)
    json.dumps(out)
    assert all(f["points"] >= 20 for f in out)
