from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class EmailLog(Base):
    __tablename__ = "email_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    report_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    to_email: Mapped[str] = mapped_column(String, nullable=False)
    cc_email: Mapped[str] = mapped_column(String, nullable=True)

    subject: Mapped[str] = mapped_column(String, nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=True)

    pdf_path: Mapped[str] = mapped_column(String, nullable=True)

    sent: Mapped[str] = mapped_column(String, default="False")
    reason: Mapped[str] = mapped_column(Text, nullable=True)

    sent_at: Mapped[str] = mapped_column(String, nullable=False)