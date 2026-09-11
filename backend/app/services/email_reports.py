import smtplib
from email.message import EmailMessage
from pathlib import Path

from app.core.config import settings


def send_report_pdf_email(
    to_email: str,
    subject: str,
    body: str,
    pdf_path: Path,
    cc_email: str | None = None,
) -> dict:
    if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
        return {
            "sent": False,
            "reason": "SMTP credentials are not configured.",
            "to_email": to_email,
            "cc_email": cc_email,
            "pdf_path": str(pdf_path),
        }

    if not pdf_path.exists():
        return {
            "sent": False,
            "reason": "PDF file does not exist.",
            "to_email": to_email,
            "cc_email": cc_email,
            "pdf_path": str(pdf_path),
        }

    try:
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
        message["To"] = to_email

        if cc_email:
            message["Cc"] = cc_email

        message.set_content(body)

        with open(pdf_path, "rb") as pdf_file:
            message.add_attachment(
                pdf_file.read(),
                maintype="application",
                subtype="pdf",
                filename=pdf_path.name,
            )

        recipients = [to_email]
        if cc_email:
            recipients.append(cc_email)

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            smtp.send_message(message, to_addrs=recipients)

        return {
            "sent": True,
            "to_email": to_email,
            "cc_email": cc_email,
            "pdf_path": str(pdf_path),
        }

    except smtplib.SMTPAuthenticationError:
        return {
            "sent": False,
            "reason": "SMTP authentication failed. Use a Gmail App Password, not your normal Gmail password.",
            "to_email": to_email,
            "cc_email": cc_email,
            "pdf_path": str(pdf_path),
        }

    except Exception as error:
        return {
            "sent": False,
            "reason": f"Email sending failed: {str(error)}",
            "to_email": to_email,
            "cc_email": cc_email,
            "pdf_path": str(pdf_path),
        }