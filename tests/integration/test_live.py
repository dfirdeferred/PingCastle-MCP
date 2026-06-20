import os
import pytest

from pingcastle_mcp.config import load_config
from pingcastle_mcp.enterprise_client import EnterpriseClient

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_LIVE") != "1",
    reason="set RUN_LIVE=1 (and PINGCASTLE_* env) to run live tests",
)


async def test_live_login_and_domains():
    cfg = load_config()
    async with EnterpriseClient(cfg) as c:
        header = await c.login()
        assert header.startswith("Bearer ")
        domains = await c.list_domains()
        assert len(domains) >= 1


async def test_live_latest_report_summary():
    from pingcastle_mcp import models
    cfg = load_config()
    async with EnterpriseClient(cfg) as c:
        domains = await c.list_domains()
        report = await c.get_latest_report(domains[0].id)
    summary = models.summarize_report(report)
    assert summary.global_score is not None
