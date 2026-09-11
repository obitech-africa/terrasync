from dataclasses import dataclass
from typing import Any

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models import AIFinding, InspectionReport


@dataclass(frozen=True)
class Rule:
    field: str
    label: str
    minimum: float | None = None
    maximum: float | None = None
    severity: str = "High"


NUMERIC_RULES = (
    Rule("tower_tilt_deg", "Tower tilt", maximum=1.5, severity="High"),
    Rule("earth_resistance_ohm", "Earth resistance", maximum=5.0, severity="Critical"),
    Rule("battery_voltage_v", "Battery voltage", minimum=46.0, maximum=58.0, severity="High"),
    Rule("temperature_c", "Cabinet temperature", maximum=45.0, severity="High"),
)

CRITICAL_TERMS = {
    "collapse": "Critical structural instability mentioned",
    "fire": "Fire or fire damage mentioned",
    "exposed live": "Potential exposed live electrical hazard",
    "severe corrosion": "Severe corrosion mentioned",
    "fall hazard": "Fall hazard mentioned",
    "unsafe": "Unsafe condition explicitly mentioned",
}


def _finding(category: str, severity: str, title: str, detail: str, field: str | None = None, confidence: float = 0.95) -> dict:
    return {
        "category": category,
        "severity": severity,
        "title": title,
        "detail": detail,
        "field": field,
        "confidence": confidence,
    }


def screen_report(report: InspectionReport) -> tuple[int, str, list[dict[str, Any]]]:
    """Run an offline-capable hybrid rules/anomaly pre-screen on an inspection report."""
    answers = report.answers or {}
    evidence = report.evidence or []
    findings: list[dict[str, Any]] = []

    required = ("structural_condition", "electrical_condition", "safety_condition")
    for field in required:
        value = answers.get(field)
        if value in (None, "", []):
            findings.append(
                _finding(
                    "completeness",
                    "Medium",
                    f"Missing {field.replace('_', ' ')}",
                    "Required inspection evidence is incomplete.",
                    field,
                    1.0,
                )
            )

    if report.latitude is None or report.longitude is None:
        findings.append(
            _finding(
                "verification",
                "Medium",
                "Missing inspection location",
                "No GPS coordinates were supplied for this inspection.",
                confidence=1.0,
            )
        )

    verified_photos = [
        item
        for item in evidence
        if isinstance(item, dict)
        and item.get("kind") == "photo"
        and item.get("source") == "live_camera"
        and item.get("sha256")
        and item.get("captured_at")
        and item.get("latitude") is not None
        and item.get("longitude") is not None
    ]
    if not verified_photos:
        findings.append(
            _finding(
                "verification",
                "Critical",
                "Missing verified camera evidence",
                "Submission does not contain a live camera capture bound to location, time and an integrity hash.",
                confidence=1.0,
            )
        )

    for rule in NUMERIC_RULES:
        raw = answers.get(rule.field)
        if raw in (None, ""):
            continue
        try:
            value = float(raw)
        except (TypeError, ValueError):
            findings.append(
                _finding(
                    "consistency",
                    "Medium",
                    f"Invalid {rule.label.lower()}",
                    f"Expected a numeric value but received {raw!r}.",
                    rule.field,
                    1.0,
                )
            )
            continue

        abnormal = (
            (rule.minimum is not None and value < rule.minimum)
            or (rule.maximum is not None and value > rule.maximum)
        )
        if abnormal:
            bounds = []
            if rule.minimum is not None:
                bounds.append(f"minimum {rule.minimum}")
            if rule.maximum is not None:
                bounds.append(f"maximum {rule.maximum}")
            findings.append(
                _finding(
                    "abnormal_reading",
                    rule.severity,
                    f"Abnormal {rule.label.lower()}",
                    f"Recorded value {value:g}; expected {' and '.join(bounds)}.",
                    rule.field,
                    0.99,
                )
            )

    text_blob = " ".join(
        str(value).lower()
        for value in [report.summary, *answers.values()]
        if value is not None
    )
    for term, title in CRITICAL_TERMS.items():
        if term in text_blob:
            findings.append(
                _finding(
                    "safety",
                    "Critical",
                    title,
                    f"The submitted report contains the safety-risk phrase “{term}”. Coordinator review is required.",
                    confidence=0.94,
                )
            )

    condition_values = {
        str(answers.get("structural_condition", "")).lower(),
        str(answers.get("electrical_condition", "")).lower(),
        str(answers.get("safety_condition", "")).lower(),
    }
    if condition_values.intersection({"critical", "dangerous", "failed", "unsafe"}):
        findings.append(
            _finding(
                "critical_defect",
                "Critical",
                "Critical condition selected",
                "One or more inspection condition fields indicate a critical or unsafe state.",
                confidence=0.98,
            )
        )

    severity_weight = {"Low": 8, "Medium": 15, "High": 28, "Critical": 45}
    risk_score = min(100, sum(severity_weight.get(item["severity"], 0) for item in findings))
    critical_count = sum(item["severity"] == "Critical" for item in findings)
    high_count = sum(item["severity"] == "High" for item in findings)

    if not findings:
        summary = "Pre-screen passed: no completeness, consistency, abnormal-reading or critical-risk flags detected."
    else:
        summary = (
            f"Pre-screen found {len(findings)} issue(s): "
            f"{critical_count} critical, {high_count} high priority. "
            "Human coordinator review is required before approval."
        )
    return risk_score, summary, findings


def persist_screening(db: Session, report: InspectionReport) -> list[AIFinding]:
    """Replace prior findings with the latest pre-screening result."""
    score, summary, findings = screen_report(report)
    db.execute(delete(AIFinding).where(AIFinding.report_id == report.id))
    persisted = [AIFinding(report_id=report.id, **item) for item in findings]
    db.add_all(persisted)
    report.ai_risk_score = score
    report.ai_summary = summary
    report.ai_status = "screened"
    db.add(report)
    db.commit()
    for item in persisted:
        db.refresh(item)
    return persisted
