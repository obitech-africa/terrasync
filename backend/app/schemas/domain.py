from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class SiteCreate(BaseModel):
    code: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=255)
    region: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class SiteOut(SiteCreate, ORMModel):
    id: str
    created_at: datetime


class WorkOrderCreate(BaseModel):
    work_order_no: str = Field(min_length=3, max_length=80)
    site_id: str
    report_type: str = "General Inspection"
    priority: Literal["Low", "Medium", "High", "Critical"] = "Medium"
    status: str = "Assigned"
    assigned_to: str | None = None
    assigned_user_id: str | None = None
    due_at: datetime | None = None


class WorkOrderOut(WorkOrderCreate, ORMModel):
    id: str
    created_at: datetime


class EvidenceItem(BaseModel):
    kind: Literal["photo"] = "photo"
    source: Literal["live_camera"] = "live_camera"
    name: str
    evidence_id: str = Field(min_length=3, max_length=100)
    sha256: str = Field(min_length=64, max_length=64)
    mime_type: Literal["image/jpeg", "image/png"] = "image/jpeg"
    content_base64: str = Field(min_length=8)
    captured_at: datetime
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    accuracy_m: float = Field(ge=0, le=10000)
    device_id: str = Field(min_length=3, max_length=100)
    inspector_name: str = Field(min_length=2, max_length=120)
    work_order_no: str = Field(min_length=3, max_length=80)



class AssetCreate(BaseModel):
    client_id: str = Field(min_length=3, max_length=64)
    work_order_id: str
    site_id: str
    asset_type: str = Field(min_length=2, max_length=120)
    manufacturer: str | None = None
    model: str | None = None
    serial_number: str | None = None
    quantity: int = Field(default=1, ge=1, le=10000)
    height_or_elevation: str | None = None
    dimensions: str | None = None
    position: str | None = None
    condition: Literal["Good", "Fair", "Poor", "Critical"] = "Good"
    notes: str | None = None
    source: Literal["client_supplied", "on_site"] = "on_site"
    evidence: list[EvidenceItem] = Field(default_factory=list)


class AssetOut(ORMModel):
    id: str
    client_id: str
    work_order_id: str
    site_id: str
    asset_type: str
    manufacturer: str | None
    model: str | None
    serial_number: str | None
    quantity: int
    height_or_elevation: str | None
    dimensions: str | None
    position: str | None
    condition: str
    notes: str | None
    source: str
    evidence: list[dict[str, Any]]
    created_by_user_id: str | None
    created_at: datetime
    updated_at: datetime


class ReviewDecision(BaseModel):
    decision: Literal["approve", "return"]
    note: str | None = Field(default=None, max_length=2000)


class ReportCreate(BaseModel):
    client_id: str = Field(min_length=3, max_length=64)
    work_order_id: str
    site_id: str
    inspector_name: str = Field(min_length=2, max_length=120)
    report_type: str = "General Inspection"
    summary: str | None = None
    answers: dict[str, Any] = Field(default_factory=dict)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    captured_at: datetime | None = None
    submit: bool = False

    @model_validator(mode="after")
    def validate_verified_submission(self):
        """Require capture-only, location-bound evidence for submitted reports."""
        if not self.submit:
            return self
        if not self.evidence:
            raise ValueError("Submitted reports require at least one verified live camera capture.")

        first = self.evidence[0]
        if self.latitude is None or self.longitude is None or self.captured_at is None:
            raise ValueError("Submitted reports require capture time and location.")
        if abs(self.latitude - first.latitude) > 1e-7 or abs(self.longitude - first.longitude) > 1e-7:
            raise ValueError("Report location must match the verified camera capture.")
        if self.captured_at != first.captured_at:
            raise ValueError("Report capture time must match the verified camera capture.")
        if self.inspector_name != first.inspector_name:
            raise ValueError("Inspector identity must match the verified camera capture.")
        return self


class ReportUpdate(BaseModel):
    summary: str | None = None
    answers: dict[str, Any] | None = None
    evidence: list[EvidenceItem] | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    status: str | None = None
    revision: int = Field(ge=1)


class ReportOut(ORMModel):
    id: str
    client_id: str
    report_no: str
    work_order_id: str
    site_id: str
    inspector_name: str
    report_type: str
    status: str
    summary: str | None
    answers: dict[str, Any]
    evidence: list[dict[str, Any]]
    latitude: float | None
    longitude: float | None
    captured_at: datetime | None
    submitted_at: datetime | None
    revision: int
    ai_status: str
    ai_risk_score: int
    ai_summary: str | None
    created_at: datetime
    updated_at: datetime


class FindingOut(ORMModel):
    id: str
    report_id: str
    category: str
    severity: str
    title: str
    detail: str
    field: str | None
    confidence: float
    acknowledged: bool
    created_at: datetime


class DefectCreate(BaseModel):
    category: str
    severity: Literal["Low", "Medium", "High", "Critical"]
    description: str = Field(min_length=3)
    recommendation: str | None = None


class DefectOut(DefectCreate, ORMModel):
    id: str
    report_id: str
    status: str
    created_at: datetime


class SyncMutation(BaseModel):
    mutation_id: str
    entity: Literal["report"]
    operation: Literal["upsert"]
    payload: ReportCreate


class SyncPushRequest(BaseModel):
    mutations: list[SyncMutation] = Field(default_factory=list)


class SyncMutationResult(BaseModel):
    mutation_id: str
    status: Literal["applied", "duplicate", "error"]
    entity_id: str | None = None
    message: str | None = None


class SyncPushResponse(BaseModel):
    results: list[SyncMutationResult]
    cursor: int


class SyncPullResponse(BaseModel):
    cursor: int
    changes: list[dict[str, Any]]
