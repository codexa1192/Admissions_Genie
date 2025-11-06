"""
Document parser service for extracting clinical data from discharge documents.
Uses local libraries (PyPDF2, python-docx, pytesseract) plus Azure OpenAI for intelligent extraction.
"""

import os
import json
from typing import Dict, List, Optional
from PIL import Image
import PyPDF2
import docx
import pytesseract
from openai import AzureOpenAI

from config.settings import Config


class DocumentParser:
    """Parser for discharge documents (PDF, Word, images)."""

    def __init__(self):
        """Initialize document parser with Azure OpenAI client (if configured)."""
        # Check if Azure OpenAI is configured
        if Config.AZURE_OPENAI_API_KEY and Config.AZURE_OPENAI_ENDPOINT:
            self.client = AzureOpenAI(
                api_key=Config.AZURE_OPENAI_API_KEY,
                api_version=Config.AZURE_OPENAI_API_VERSION,
                azure_endpoint=Config.AZURE_OPENAI_ENDPOINT
            )
            self.deployment_name = Config.AZURE_OPENAI_DEPLOYMENT_NAME
            self.ai_enabled = True
        else:
            self.client = None
            self.deployment_name = None
            self.ai_enabled = False

    def parse_file(self, file_path: str) -> str:
        """
        Parse a file and extract text content.

        Args:
            file_path: Path to the file

        Returns:
            Extracted text content

        Raises:
            ValueError: If file type is not supported
        """
        ext = os.path.splitext(file_path)[1].lower()

        if ext == '.pdf':
            return self._parse_pdf(file_path)
        elif ext in ['.docx', '.doc']:
            return self._parse_docx(file_path)
        elif ext in ['.jpg', '.jpeg', '.png', '.tiff']:
            return self._parse_image(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    def _parse_pdf(self, file_path: str) -> str:
        """Extract text from PDF using PyPDF2."""
        text = []
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text.append(page_text)
        except Exception as e:
            raise ValueError(f"Failed to parse PDF: {e}")

        return '\n'.join(text)

    def _parse_docx(self, file_path: str) -> str:
        """Extract text from Word document using python-docx."""
        try:
            doc = docx.Document(file_path)
            text = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text.append(paragraph.text)
            return '\n'.join(text)
        except Exception as e:
            raise ValueError(f"Failed to parse DOCX: {e}")

    def _parse_image(self, file_path: str) -> str:
        """Extract text from image using Tesseract OCR."""
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            raise ValueError(f"Failed to parse image with OCR: {e}")

    def extract_clinical_features(self, document_text: str) -> Dict:
        """
        Extract structured clinical features from document text using Azure OpenAI.

        This is the ONLY cloud API call - extracts:
        - ICD-10 codes
        - Medications
        - Therapy notes
        - Functional status
        - Special services (IV ABX, wound vac, dialysis, etc.)

        Args:
            document_text: Raw text from document

        Returns:
            Dictionary with extracted features

        Cost: ~$0.50-1.00 per admission (GPT-4 Turbo)
        """
        # If Azure OpenAI is not configured, return error
        if not self.ai_enabled:
            raise ValueError(
                "Azure OpenAI not configured. Document upload requires Azure OpenAI API credentials. "
                "The application is running in DEMO MODE with pre-loaded sample admissions only."
            )
        extraction_prompt = f"""
You are a clinical data extraction expert for SNF admissions. Extract the following information from this discharge document:

1. **Primary Diagnosis**: The main ICD-10 code (format: A00.0)
2. **Comorbidities**: List all additional ICD-10 codes mentioned
3. **Medications**: List all medications with dosages
4. **Functional Status**: Any ADL scores, mobility descriptions, or Section GG scores
5. **Therapy Needs**: PT, OT, SLP requirements or evaluations mentioned
6. **Special Services**: Check for:
   - IV antibiotics (IV ABX)
   - Wound vac
   - Dialysis
   - Tracheostomy care
   - Feeding tube
   - Oxygen therapy
   - Bariatric care
7. **Estimated Length of Stay**: Any mention of expected LOS
8. **Authorization Status**: Any mention of insurance authorization or benefit days remaining
9. **Clinical Notes**: Key clinical observations (wounds, falls risk, cognitive status)

Return ONLY a valid JSON object with these keys:
{{
  "primary_diagnosis": "ICD-10 code",
  "comorbidities": ["ICD-10 code 1", "ICD-10 code 2", ...],
  "medications": ["medication 1", "medication 2", ...],
  "functional_status": {{
    "adl_score": number or null,
    "mobility": "description",
    "cognitive_status": "description"
  }},
  "therapy_needs": {{
    "pt": true/false,
    "ot": true/false,
    "slp": true/false,
    "notes": "any therapy evaluation notes"
  }},
  "special_services": {{
    "iv_abx": true/false,
    "wound_vac": true/false,
    "dialysis": true/false,
    "trach": true/false,
    "feeding_tube": true/false,
    "oxygen": true/false,
    "bariatric": true/false
  }},
  "estimated_los": number or null,
  "authorization_status": "granted/pending/unknown",
  "benefit_days_remaining": number or null,
  "clinical_notes": "brief summary of key clinical observations"
}}

Document text:
{document_text[:8000]}  # Limit to 8000 chars to control costs
"""

        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "You are a clinical data extraction expert. Return only valid JSON."},
                    {"role": "user", "content": extraction_prompt}
                ],
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=2000
            )

            # Parse JSON response
            extracted_json = response.choices[0].message.content.strip()

            # Remove markdown code blocks if present
            if extracted_json.startswith('```json'):
                extracted_json = extracted_json[7:]
            if extracted_json.startswith('```'):
                extracted_json = extracted_json[3:]
            if extracted_json.endswith('```'):
                extracted_json = extracted_json[:-3]

            extracted_data = json.loads(extracted_json.strip())
            return extracted_data

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse Azure OpenAI response as JSON: {e}")
        except Exception as e:
            raise ValueError(f"Azure OpenAI extraction failed: {e}")

    def parse_and_extract(self, file_path: str) -> Dict:
        """
        Parse a document file and extract clinical features.

        Args:
            file_path: Path to the document file

        Returns:
            Dictionary with extracted clinical features
        """
        # Step 1: Extract text from document (local, free)
        document_text = self.parse_file(file_path)

        # Step 2: Extract structured features using AI (Azure OpenAI, costs ~$0.50-1.00)
        extracted_features = self.extract_clinical_features(document_text)

        return extracted_features


# Example usage
if __name__ == '__main__':
    # Test the parser
    parser = DocumentParser()

    # Test with a sample document (you'll need to provide a real document)
    # result = parser.parse_and_extract('/path/to/sample/discharge_summary.pdf')
    # print(json.dumps(result, indent=2))

    print("DocumentParser initialized successfully")
