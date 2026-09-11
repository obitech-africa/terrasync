from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.demo import seed_demo

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/seed")
def seed(db: Session = Depends(get_db)) -> dict[str, str]:
    return seed_demo(db)
