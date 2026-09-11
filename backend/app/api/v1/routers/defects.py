from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Defect, InspectionReport
from app.schemas.domain import DefectCreate, DefectOut

router = APIRouter(prefix="/reports/{report_id}/defects", tags=["defects"])


@router.get("", response_model=list[DefectOut])
def list_defects(report_id: str, db: Session = Depends(get_db)) -> list[Defect]:
    return list(db.scalars(select(Defect).where(Defect.report_id == report_id)))


@router.post("", response_model=DefectOut, status_code=status.HTTP_201_CREATED)
def create_defect(report_id: str, payload: DefectCreate, db: Session = Depends(get_db)) -> Defect:
    if not db.get(InspectionReport, report_id):
        raise HTTPException(status_code=404, detail="Report not found")
    defect = Defect(report_id=report_id, **payload.model_dump())
    db.add(defect)
    db.commit()
    db.refresh(defect)
    return defect
