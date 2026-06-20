from __future__ import annotations
from dataclasses import dataclass

_CATEGORY_SCORE_KEYS = {
    "stale": "staleObjectsScore",
    "privileged": "privilegiedGroupScore",  # PingCastle's spelling
    "trust": "trustScore",
    "anomaly": "anomalyScore",
}


@dataclass
class Domain:
    id: int
    name: str
    last_report_id: int | None
    number_of_reports: int


@dataclass
class ReportListItem:
    id: int
    generation: str
    global_score: int
    stale_objects_score: int
    privileged_group_score: int
    trust_score: int
    anomaly_score: int
    maturity_level: int


@dataclass
class Finding:
    risk_id: str
    model: str
    category: str
    level: str
    points: int
    rationale: str
    details: list | None


@dataclass
class ReportSummary:
    report_id: int | None
    domain_fqdn: str
    generation: str
    global_score: int
    category_scores: dict[str, int]
    maturity_level: int
    findings_by_category: dict[str, int]
    top_findings: list[Finding]


@dataclass
class Comparison:
    score_deltas: dict[str, int]
    new: list[Finding]
    resolved: list[Finding]
    unchanged: list[str]


@dataclass
class TrendPoint:
    report_id: int
    generation: str
    global_score: int


def parse_domain(d: dict) -> Domain:
    return Domain(
        id=d["id"],
        name=d["name"],
        last_report_id=d.get("lastReportID"),
        number_of_reports=d.get("numberOfReport", 0),
    )


def parse_report_list_item(d: dict) -> ReportListItem:
    return ReportListItem(
        id=d["id"],
        generation=d.get("generation", ""),
        global_score=d.get("globalScore", 0),
        stale_objects_score=d.get("staleObjectsScore", 0),
        privileged_group_score=d.get("privilegiedGroupScore", 0),
        trust_score=d.get("trustScore", 0),
        anomaly_score=d.get("anomalyScore", 0),
        maturity_level=d.get("maturityLevel", 0),
    )


def parse_finding(d: dict) -> Finding:
    return Finding(
        risk_id=d["riskId"],
        model=d.get("modelAsString") or d.get("model", ""),
        category=d.get("categoryAsString") or d.get("category", ""),
        level=d.get("level", ""),
        points=d.get("points", 0),
        rationale=d.get("rationale", ""),
        details=d.get("details"),
    )


def _rules(report: dict) -> list[dict]:
    return report.get("riskRules") or []


def parse_findings(report: dict, category: str | None = None,
                   min_points: int = 0) -> list[Finding]:
    out = []
    for r in _rules(report):
        f = parse_finding(r)
        if category and f.category != category:
            continue
        if f.points < min_points:
            continue
        out.append(f)
    return out


def summarize_report(report: dict, top_n: int = 10, report_id: int | None = None) -> ReportSummary:
    findings = [parse_finding(r) for r in _rules(report)]
    by_category: dict[str, int] = {}
    for f in findings:
        by_category[f.category] = by_category.get(f.category, 0) + 1
    top = sorted(findings, key=lambda f: f.points, reverse=True)[:top_n]
    category_scores = {k: report.get(v, 0) for k, v in _CATEGORY_SCORE_KEYS.items()}
    resolved_id = report_id if report_id is not None else (report.get("id") or report.get("reportID"))
    return ReportSummary(
        report_id=resolved_id,
        domain_fqdn=report.get("domainFQDN", ""),
        generation=report.get("generationDate", report.get("generation", "")),
        global_score=report.get("globalScore", 0),
        category_scores=category_scores,
        maturity_level=report.get("maturityLevel", 0),
        findings_by_category=by_category,
        top_findings=top,
    )


def compare_reports(a: dict, b: dict) -> Comparison:
    """Compare report `a` (current) against `b` (previous)."""
    a_rules = {r["riskId"]: parse_finding(r) for r in _rules(a)}
    b_rules = {r["riskId"]: parse_finding(r) for r in _rules(b)}
    new = [a_rules[k] for k in a_rules.keys() - b_rules.keys()]
    resolved = [b_rules[k] for k in b_rules.keys() - a_rules.keys()]
    unchanged = sorted(a_rules.keys() & b_rules.keys())
    deltas = {"global": a.get("globalScore", 0) - b.get("globalScore", 0)}
    for name, key in _CATEGORY_SCORE_KEYS.items():
        deltas[name] = a.get(key, 0) - b.get(key, 0)
    return Comparison(score_deltas=deltas, new=new, resolved=resolved, unchanged=unchanged)


def trend_from_reports(reports: list[dict]) -> list[TrendPoint]:
    return [
        TrendPoint(
            report_id=r["id"],
            generation=r.get("generation", ""),
            global_score=r.get("globalScore", 0),
        )
        for r in reports
    ]
