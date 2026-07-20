import os
import uuid
from pathlib import Path
from fastapi import UploadFile
from app.core.exceptions import AppException

UPLOAD_DIR = Path("./uploads/resumes")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class StorageService:
    """Service for handling file uploads (Local Storage / AWS S3 ready)."""

    @staticmethod
    async def save_resume_file(company_id: uuid.UUID, file: UploadFile) -> str:
        """Save file to local disk under company tenant directory and return file path."""
        try:
            tenant_dir = UPLOAD_DIR / str(company_id)
            tenant_dir.mkdir(parents=True, exist_ok=True)

            ext = Path(file.filename or "resume.pdf").suffix.lower()
            unique_filename = f"{uuid.uuid4()}{ext}"
            file_path = tenant_dir / unique_filename

            content = await file.read()
            await file.seek(0)  # reset cursor for downstream processing

            with open(file_path, "wb") as f:
                f.write(content)

            return str(file_path)
        except Exception as e:
            raise AppException(
                message=f"Failed to save upload file: {str(e)}",
                error_code="STORAGE_SAVE_ERROR",
            )
