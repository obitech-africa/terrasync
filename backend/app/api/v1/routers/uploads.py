from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status


router = APIRouter()


ALLOWED_IMAGE_TYPES = [
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
]

MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

UPLOAD_ROOT = Path("uploads")
EVIDENCE_DIR = UPLOAD_ROOT / "evidence"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/evidence", response_model=dict, status_code=status.HTTP_201_CREATED)
async def upload_evidence_photo(
    file: UploadFile = File(...),
    report_id: str = Form(...),
    site_id: str = Form(...),
    section_id: str = Form(...),
    item_id: str = Form(...),
    field_key: str = Form(...),
    uploaded_by: str = Form(...),
):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG, PNG, and WEBP images are allowed.",
        )

    file_bytes = await file.read()

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File is too large. Maximum allowed size is {MAX_FILE_SIZE_MB}MB.",
        )

    original_name = file.filename or "evidence_photo"
    extension = Path(original_name).suffix.lower()

    if extension not in [".jpg", ".jpeg", ".png", ".webp"]:
        extension = ".jpg"

    now = datetime.now(timezone.utc)
    safe_report_id = report_id.replace("/", "-").replace("\\", "-")
    safe_site_id = site_id.replace("/", "-").replace("\\", "-")

    folder = EVIDENCE_DIR / safe_site_id / safe_report_id
    folder.mkdir(parents=True, exist_ok=True)

    file_name = f"{section_id}_{item_id}_{field_key}_{uuid4().hex}{extension}"
    file_path = folder / file_name

    with open(file_path, "wb") as output_file:
        output_file.write(file_bytes)

    file_url = f"/uploads/evidence/{safe_site_id}/{safe_report_id}/{file_name}"

    return {
        "message": "Evidence photo uploaded successfully.",
        "report_id": report_id,
        "site_id": site_id,
        "section_id": section_id,
        "item_id": item_id,
        "field_key": field_key,
        "uploaded_by": uploaded_by,
        "content_type": file.content_type,
        "file_name": file_name,
        "file_url": file_url,
        "uploaded_at": now.isoformat(),
    }


@router.get("/evidence/test", response_model=dict)
def upload_test():
    return {
        "status": "ok",
        "message": "Evidence upload endpoint is available.",
        "allowed_image_types": ALLOWED_IMAGE_TYPES,
        "max_file_size_mb": MAX_FILE_SIZE_MB,
    }