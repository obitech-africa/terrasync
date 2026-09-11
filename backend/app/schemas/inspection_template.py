from typing import Any, Optional

from pydantic import BaseModel


class InspectionTemplateBase(BaseModel):
    template_id: str
    name: str

    industry: str
    company_type: str
    asset_type: str
    inspection_type: str

    category: str
    version: str = "1.0"
    status: str = "Active"

    template_info: dict[str, Any]
    sections: list[dict[str, Any]]


class InspectionTemplateCreate(InspectionTemplateBase):
    pass


class InspectionTemplateRead(InspectionTemplateBase):
    id: int

    class Config:
        from_attributes = True


class TemplateSelectRequest(BaseModel):
    industry: str
    company_type: str
    asset_type: str
    inspection_type: str
    company_name: Optional[str] = None