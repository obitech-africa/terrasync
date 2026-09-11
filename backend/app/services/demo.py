from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_secret
from app.models import ActivationCode, Asset, InspectionReport, Site, User, WorkOrder
from app.services.ai_screening import persist_screening


def seed_demo(db: Session) -> dict[str, str]:
    """Create commercial demo users, assignments, and one AI-screened report."""
    definitions = {
        "field.tech": ("Bogere Francis", "FIELD_TECHNICIAN", None, "FE-UG-0241"),
        "coordinator": ("Sarah Namuli", "COORDINATOR", "demo123", "CO-UG-0042"),
        "supervisor": ("Daniel Okello", "SUPERVISOR", "demo123", "SV-UG-0014"),
        "admin": ("TerraSync Admin", "ADMIN", "demo123", "ADM-001"),
    }

    seeded_users: dict[str, User] = {}
    for username, (full_name, role, password, staff_no) in definitions.items():
        user = db.scalar(select(User).where(User.username == username))
        if not user:
            user = User(
                username=username,
                full_name=full_name,
                email=f"{username}@terrasync.demo",
                phone="+256 700 000 000",
                company="TerraSync Demo",
                staff_no=staff_no,
                role=role,
                password_hash=hash_secret(password) if password else None,
                certifications=(
                    [
                        {
                            "name": "Certified Rigger",
                            "id": "CR-UG-2026",
                            "expires": "2027-06-30",
                        }
                    ]
                    if role == "FIELD_TECHNICIAN"
                    else []
                ),
            )
            db.add(user)
            db.flush()
        seeded_users[username] = user

    technician = seeded_users["field.tech"]

    active_code = db.scalar(
        select(ActivationCode).where(
            ActivationCode.user_id == technician.id,
            ActivationCode.used_at.is_(None),
        )
    )
    if not active_code:
        db.add(
            ActivationCode(
                user_id=technician.id,
                code_hash=hash_secret("246810"),
                expires_at=datetime.now(timezone.utc) + timedelta(days=365),
            )
        )

    site = db.scalar(select(Site).where(Site.code == "KMP-001"))
    if not site:
        site = Site(
            code="KMP-001",
            name="Kampala Central Telecom Site",
            region="Central",
            latitude=0.3476,
            longitude=32.5825,
        )
        db.add(site)
        db.flush()

    work_order = db.scalar(
        select(WorkOrder).where(WorkOrder.work_order_no == "WO-2026-0001")
    )
    if not work_order:
        work_order = WorkOrder(
            work_order_no="WO-2026-0001",
            site_id=site.id,
            report_type="Telecom Tower Inspection",
            priority="High",
            status="Assigned",
            assigned_to=technician.full_name,
            assigned_user_id=technician.id,
            due_at=datetime.now(timezone.utc) + timedelta(days=2),
        )
        db.add(work_order)
        db.flush()

    if not db.scalar(select(Asset).where(Asset.client_id == "demo-asset-rru")):
        db.add(
            Asset(
                client_id="demo-asset-rru",
                work_order_id=work_order.id,
                site_id=site.id,
                asset_type="RRU",
                manufacturer="ZTE",
                model="R8854",
                serial_number="ZT-RRU-88241",
                quantity=3,
                height_or_elevation="53 m",
                dimensions="480 × 320 × 165 mm",
                position="Tower Leg B",
                condition="Good",
                source="client_supplied",
                evidence=[],
            )
        )
    if not db.scalar(select(Asset).where(Asset.client_id == "demo-asset-antenna")):
        db.add(
            Asset(
                client_id="demo-asset-antenna",
                work_order_id=work_order.id,
                site_id=site.id,
                asset_type="Antenna",
                manufacturer="Ace",
                model="XXDW-65-33-iVT",
                serial_number="ANT-608241-01",
                quantity=3,
                height_or_elevation="49 m",
                position="Sector A/B/C",
                condition="Good",
                source="client_supplied",
                evidence=[],
            )
        )
    db.flush()

    report = db.scalar(
        select(InspectionReport).where(
            InspectionReport.client_id == "demo-risk-report"
        )
    )
    if not report:
        report = InspectionReport(
            client_id="demo-risk-report",
            report_no="RPT-2026-DEMO-001",
            work_order_id=work_order.id,
            site_id=site.id,
            inspector_name=technician.full_name,
            report_type="Telecom Tower Inspection",
            status="Submitted",
            summary=(
                "Severe corrosion near base plate. "
                "Area may be unsafe until reviewed."
            ),
            answers={
                "structural_condition": "Poor",
                "electrical_condition": "Good",
                "safety_condition": "Unsafe",
                "tower_tilt_deg": 2.2,
                "earth_resistance_ohm": 7.4,
                "battery_voltage_v": 51.8,
                "temperature_c": 34,
            },
            evidence=[],
            latitude=0.3476,
            longitude=32.5825,
            captured_at=datetime.now(timezone.utc),
            submitted_at=datetime.now(timezone.utc),
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        persist_screening(db, report)
    else:
        db.commit()

    return {
        "site_id": site.id,
        "work_order_id": work_order.id,
        "report_id": report.id,
        "technician_id": technician.id,
    }
