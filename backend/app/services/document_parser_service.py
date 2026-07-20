import fitz  # PyMuPDF
import docx
from fastapi import UploadFile
from app.core.exceptions import AppException


class DocumentParserService:
    """Service for extracting raw text from uploaded files (PDF, DOCX, TXT)."""

    @staticmethod
    async def parse_upload_file(file: UploadFile) -> str:
        filename = file.filename.lower() if file.filename else ""
        content = await file.read()

        if filename.endswith(".pdf"):
            return DocumentParserService.extract_text_from_pdf(content)
        elif filename.endswith(".docx") or filename.endswith(".doc"):
            return DocumentParserService.extract_text_from_docx(content)
        elif filename.endswith(".txt"):
            return content.decode("utf-8", errors="ignore")
        else:
            raise AppException(
                message=f"Unsupported file format for '{file.filename}'. Supported: PDF, DOCX, TXT",
                error_code="UNSUPPORTED_FILE_TYPE",
            )

    @staticmethod
    def extract_text_from_pdf(pdf_bytes: bytes) -> str:
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text() + "\n"
            return text.strip()
        except Exception as e:
            raise AppException(
                message=f"Failed to extract text from PDF document: {str(e)}",
                error_code="PDF_PARSING_ERROR",
            )

    @staticmethod
    def extract_text_from_docx(docx_bytes: bytes) -> str:
        try:
            import io
            doc = docx.Document(io.BytesIO(docx_bytes))
            text = []
            for paragraph in doc.paragraphs:
                if paragraph.text:
                    text.append(paragraph.text)
            return "\n".join(text).strip()
        except Exception as e:
            raise AppException(
                message=f"Failed to extract text from DOCX document: {str(e)}",
                error_code="DOCX_PARSING_ERROR",
            )
