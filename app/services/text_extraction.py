from fastapi import UploadFile
import pdfplumber
import chardet
import logging


class TextExtractionService:
    def __init__(self) -> None:
        pass

    def determine_file_type(self, file: UploadFile) -> str:
        try:
            if not file or not file.filename:
                raise ValueError("No filename provided")
            file_name = file.filename.lower()
            if file_name.endswith(".pdf"):
                return "pdf"
            elif file_name.endswith(".txt"):
                return "txt"
            else:
                raise ValueError(
                    f"Unsupported file type. Only PDF and Text file is allowed"
                )
        except Exception as e:
            logging.error(f"Error determining file type: {e}")
            raise

    def extract_pdf_text(self, file_content: bytes) -> str:
        try:
            from io import BytesIO

            with pdfplumber.open(BytesIO(file_content)) as pdf:
                text_content = []

                for page in pdf.pages:
                    page_text = page.extract_text()

                    if page_text:
                        text_content.append(page_text)

                if not text_content:
                    raise ValueError("No text content found in PDF")

                full_text = "\n\n".join(text_content)

                logging.info(
                    f"Successfully extracted text from PDF: {len(full_text)} characters"
                )
                return full_text.strip()
        except Exception as e:
            logging.error(f"Error extracting PDF text: {e}")
            raise

    async def extract_txt_text(self, file: UploadFile) -> str:
        try:
            file_content = await file.read()

            encoding_result = chardet.detect(file_content)
            encoding = encoding_result.get("encoding", "utf-8")
            confidence = encoding_result.get("confidence", 0)

            logging.info(
                f"Detected encoding: {encoding} (confidence: {confidence:.2f})"
            )

            # fallback to utf-8
            try:
                text_content = file_content.decode(encoding)
            except (UnicodeDecodeError, TypeError):
                logging.warning(f"Failed to decode with {encoding},trying utf-8")
                text_content = file_content.decode("utf-8", errors="ignore")

            if not text_content.strip():
                raise ValueError("Text file appears to be empty")
            logging.info(f"Successfully extracted text: {len(text_content)} characters")
            return text_content.strip()
        except Exception as e:
            logging.error(f"Error extracting text file content: {e}")
            raise

    async def extract_text_from_file(self, file: UploadFile) -> str:
        try:
            self.validate_file(file)

            file_type = self.determine_file_type(file)

            if file_type == "pdf":
                file_content = await file.read()
                return self.extract_pdf_text(file_content)
            elif file_type == "txt":
                await file.seek(0)
                return await self.extract_txt_text(file)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            logging.error(f"Error extracting text from file: {e}")
            raise

    def validate_file(self, file: UploadFile) -> bool:
        try:
            if not file or not file.filename:
                raise ValueError("No file provided")

            file_type = self.determine_file_type(file)
            if file_type not in ["pdf", "txt"]:
                raise ValueError(f"Unsupported file type: {file_type}")
            MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
            if hasattr(file, "size") and file.size > MAX_FILE_SIZE:
                raise ValueError(f"File too large. Max size: {MAX_FILE_SIZE}")

            return True
        except Exception as e:
            logging.error(f"Error Validating file: {e}")
            raise
