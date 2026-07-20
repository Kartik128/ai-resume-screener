import io
import fitz  # PyMuPDF
import docx
from PIL import Image
from loguru import logger
from fastapi import UploadFile
from app.core.exceptions import AppException

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False


class ResumeExtractorService:
    """Multi-format document text & OCR extractor for resumes (PDF, DOCX, Images, TXT)."""

    @staticmethod
    async def extract_raw_text(file: UploadFile) -> str:
        filename = (file.filename or "").lower()
        content = await file.read()
        await file.seek(0)

        if filename.endswith(".pdf"):
            return ResumeExtractorService.extract_from_pdf(content)
        elif filename.endswith(".docx") or filename.endswith(".doc"):
            return ResumeExtractorService.extract_from_docx(content)
        elif filename.endswith((".png", ".jpg", ".jpeg", ".tiff", ".bmp")):
            return ResumeExtractorService.extract_from_image(content)
        elif filename.endswith(".txt"):
            return content.decode("utf-8", errors="ignore")
        else:
            raise AppException(
                message=f"Unsupported resume format: '{file.filename}'. Allowed: PDF, DOCX, PNG, JPG, TXT",
                error_code="UNSUPPORTED_RESUME_FORMAT",
            )

    @staticmethod
    def extract_from_pdf(pdf_bytes: bytes) -> str:
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text() + "\n"
            text = text.strip()

            # Scanned PDF Fallback OCR if text length is empty or very low
            if len(text) < 50 and HAS_TESSERACT:
                logger.info("PDF appears to be scanned or image-based. Applying OCR...")
                ocr_text = ""
                for page in doc:
                    pix = page.get_pixmap()
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    ocr_text += pytesseract.image_to_string(img) + "\n"
                if len(ocr_text.strip()) > len(text):
                    return ocr_text.strip()

            return text
        except Exception as e:
            logger.error(f"Error parsing PDF: {str(e)}")
            raise AppException(message=f"Error reading PDF file: {str(e)}", error_code="PDF_READ_ERROR")

    @staticmethod
    def extract_from_docx(docx_bytes: bytes) -> str:
        try:
            doc = docx.Document(io.BytesIO(docx_bytes))
            text = [p.text for p in doc.paragraphs if p.text]
            return "\n".join(text).strip()
        except Exception as e:
            raise AppException(message=f"Error reading DOCX file: {str(e)}", error_code="DOCX_READ_ERROR")

    @staticmethod
    def extract_from_image(image_bytes: bytes) -> str:
        try:
            img = Image.open(io.BytesIO(image_bytes))
            if HAS_TESSERACT:
                return pytesseract.image_to_string(img).strip()
            else:
                logger.warning("pytesseract is not installed or Tesseract binary missing. Returning empty OCR text.")
                return "OCR text extraction unavailable"
        except Exception as e:
            raise AppException(message=f"Error reading Image file: {str(e)}", error_code="IMAGE_READ_ERROR")
