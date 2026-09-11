from typing import Any
from pydantic import BaseModel, Field


class ClientCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    code: str = Field(min_length=2, max_length=50)
    sector: str | None = None
    branding: dict[str, Any] = Field(default_factory=dict)


class ProjectCreate(BaseModel):
    client_id: str
    name: str = Field(min_length=2, max_length=180)
    code: str = Field(min_length=2, max_length=60)
    sector: str | None = None
    settings: dict[str, Any] = Field(default_factory=dict)


class TemplateCreate(BaseModel):
    client_id: str | None = None
    name: str
    slug: str
    sector: str
    category: str = "inspection"
    description: str | None = None
    definition: dict[str, Any] = Field(default_factory=dict)


class TemplateVersionCreate(BaseModel):
    definition: dict[str, Any]
    changelog: str | None = None


class AssetSchemaCreate(BaseModel):
    client_id: str | None = None
    project_id: str | None = None
    name: str
    asset_type: str
    fields: list[dict[str, Any]] = Field(default_factory=list)
    evidence_rules: dict[str, Any] = Field(default_factory=dict)


class AIRuleSetCreate(BaseModel):
    client_id: str | None = None
    project_id: str | None = None
    template_id: str | None = None
    name: str
    rules: list[dict[str, Any]] = Field(default_factory=list)
    thresholds: dict[str, Any] = Field(default_factory=dict)


class ReportLayoutCreate(BaseModel):
    client_id: str | None = None
    project_id: str | None = None
    template_id: str | None = None
    name: str
    layout: dict[str, Any] = Field(default_factory=dict)
    compression_profile: str = "standard"
