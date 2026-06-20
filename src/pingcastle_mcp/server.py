from __future__ import annotations
from dataclasses import asdict

from mcp.server.fastmcp import FastMCP

from .config import Config, load_config
from .enterprise_client import EnterpriseClient
from .scanner import Scanner, ScanResult
from .errors import ScannerError
from . import models


def build_server(config: Config) -> FastMCP:
    mcp = FastMCP("pingcastle")
    scanner = Scanner(config)

    def _client() -> EnterpriseClient:
        # Fresh client (and login) per tool call: simplest correct lifecycle for an
        # interactive stdio server; trades a per-call login for avoiding shared-state bugs.
        return EnterpriseClient(config)

    @mcp.tool()
    async def list_domains() -> list[dict]:
        """List all scanned domains/forests with their latest score and report count."""
        async with _client() as c:
            return [asdict(d) for d in await c.list_domains()]

    @mcp.tool()
    async def list_reports(domain_id: int) -> list[dict]:
        """List reports for a domain (id, date, scores, maturity level)."""
        async with _client() as c:
            return [asdict(r) for r in await c.list_reports(domain_id)]

    @mcp.tool()
    async def get_report_summary(report_id: int | None = None,
                                 domain_id: int | None = None,
                                 top_n: int = 10) -> dict:
        """Summary (scores, maturity, finding counts, top findings) for a report.
        Provide report_id, or domain_id to use that domain's latest report."""
        async with _client() as c:
            report = (await c.get_latest_report(domain_id) if report_id is None
                      else await c.get_report(report_id))
        return asdict(models.summarize_report(report, top_n=top_n, report_id=report_id))

    @mcp.tool()
    async def get_findings(report_id: int, category: str | None = None,
                           min_points: int = 0) -> list[dict]:
        """List matched risk rules for a report, filterable by category/min_points.
        Note: PingCastle's per-rule 'level' is a report detail-level, not a severity;
        severity is expressed via points, so filter with min_points."""
        async with _client() as c:
            report = await c.get_report(report_id)
        return [asdict(f) for f in models.parse_findings(
            report, category=category, min_points=min_points)]

    @mcp.tool()
    async def compare_reports(report_id_a: int, report_id_b: int) -> dict:
        """Diff report A (current) vs B (previous): new/resolved findings + score deltas."""
        async with _client() as c:
            a = await c.get_report(report_id_a)
            b = await c.get_report(report_id_b)
        cmp = models.compare_reports(a, b)
        return {
            "score_deltas": cmp.score_deltas,
            "new": [asdict(f) for f in cmp.new],
            "resolved": [asdict(f) for f in cmp.resolved],
            "unchanged": cmp.unchanged,
        }

    @mcp.tool()
    async def score_trend(domain_id: int) -> list[dict]:
        """Global score over time for a domain (one point per report)."""
        # Derived from the domain's report list (per-report scores + dates) — a cleaner
        # trend source than /api/KPIHistory (which is owner-level KPI counts).
        async with _client() as c:
            reports = await c.list_reports(domain_id)
        points = models.trend_from_reports([asdict(r) for r in reports])
        points.sort(key=lambda p: p.generation)
        return [asdict(p) for p in points]

    @mcp.tool()
    async def run_scan(server: str) -> dict:
        """Run an on-demand PingCastle healthcheck against `server` and upload to Enterprise.
        Requires PINGCASTLE_EXE_PATH (Windows host + AD reachability)."""
        try:
            result: ScanResult = await scanner.run(server=server)
            return asdict(result)
        except ScannerError as e:
            return asdict(ScanResult(False, -1, None, str(e)))

    # Test helper: fetch a registered tool's raw callable by name.
    def _tool_for(name: str):
        return {
            "list_domains": list_domains, "list_reports": list_reports,
            "get_report_summary": get_report_summary, "get_findings": get_findings,
            "compare_reports": compare_reports, "score_trend": score_trend,
            "run_scan": run_scan,
        }[name]

    mcp._tool_for = _tool_for  # type: ignore[attr-defined]
    return mcp


def run() -> None:
    config = load_config()
    mcp = build_server(config)
    mcp.run()  # stdio transport
