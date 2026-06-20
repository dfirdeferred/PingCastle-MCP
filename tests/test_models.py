import json
from pingcastle_mcp import models


def load(fixtures_dir, name):
    return json.loads((fixtures_dir / name).read_text())


def test_parse_domain(fixtures_dir):
    d = models.parse_domain(load(fixtures_dir, "domains.json")[0])
    assert d.name == "cloud.lab"
    assert d.number_of_reports > 0


def test_parse_report_list_item(fixtures_dir):
    raw = load(fixtures_dir, "reports_list.json")[0]
    item = models.parse_report_list_item(raw)
    assert item.id == raw["id"]
    assert item.global_score == raw["globalScore"]
    assert item.maturity_level == raw["maturityLevel"]


def test_summarize_report_top_findings_sorted(fixtures_dir):
    report = load(fixtures_dir, "report_full.json")
    s = models.summarize_report(report, top_n=5)
    assert s.domain_fqdn == "cloud.lab"
    assert len(s.top_findings) == 5
    pts = [f.points for f in s.top_findings]
    assert pts == sorted(pts, reverse=True)
    assert s.category_scores["anomaly"] == report["anomalyScore"]
    assert sum(s.findings_by_category.values()) == len(report["riskRules"])
    assert "Anomalies" in s.findings_by_category


def test_parse_findings_filters(fixtures_dir):
    report = load(fixtures_dir, "report_full.json")
    high = models.parse_findings(report, min_points=20)
    assert all(f.points >= 20 for f in high)
    anomalies = models.parse_findings(report, category="Anomalies")
    assert all(f.category == "Anomalies" for f in anomalies)


def test_compare_reports_diff(fixtures_dir):
    cur = load(fixtures_dir, "report_full.json")
    prev = load(fixtures_dir, "report_full_prev.json")
    c = models.compare_reports(cur, prev)
    cur_ids = {r["riskId"] for r in cur["riskRules"]}
    prev_ids = {r["riskId"] for r in prev["riskRules"]}
    assert {f.risk_id for f in c.new} == cur_ids - prev_ids
    assert {f.risk_id for f in c.resolved} == prev_ids - cur_ids
    assert c.score_deltas["global"] == cur["globalScore"] - prev["globalScore"]


def test_trend_from_reports(fixtures_dir):
    reports = load(fixtures_dir, "reports_list.json")
    points = models.trend_from_reports(reports)
    assert len(points) == len(reports)
    assert points[0].global_score == reports[0]["globalScore"]


def test_summarize_report_uses_explicit_report_id(fixtures_dir):
    report = load(fixtures_dir, "report_full.json")
    s = models.summarize_report(report, report_id=1002)
    assert s.report_id == 1002


def test_summarize_report_id_is_none_when_unknown(fixtures_dir):
    report = load(fixtures_dir, "report_full.json")  # body has no id/reportID
    s = models.summarize_report(report)
    assert s.report_id is None
