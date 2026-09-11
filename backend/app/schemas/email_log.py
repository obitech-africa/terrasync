from typing import Optional

from pydantic import BaseModel


class EmailLogRead(BaseModel):
    id: int
    report_id: str
    to_email: str
    cc_email: Optional[str] = None
    subject: Optional[str] = None
    message: Optional[str] = None
    pdf_path: Optional[str] = None
    sent: str
    reason: Optional[str] = None
    sent_at: str

    class Config:
        from_attributes = True