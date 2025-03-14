from typing import Dict, Any
import json
from openai import OpenAI
import pytesseract
from PIL import Image
import io
import base64
from ..interfaces import IEvidenceProcessor, RefundPolicy
from loguru import logger
from datetime import datetime

class OpenAIEvidenceProcessor(IEvidenceProcessor):
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    async def process_receipt(self, receipt_data: bytes) -> Dict[str, Any]:
        """Process receipt and extract relevant information"""
        try:
            # First try OCR to extract text from receipt
            receipt_text = self._perform_ocr(receipt_data)
            
            # Use GPT-4 to extract structured information
            prompt = f"""
            Extract key information from this receipt text:
            
            Receipt Text:
            {receipt_text}
            
            Extract and format as JSON with these keys:
            - order_id: string (any order/transaction ID)
            - date: string (purchase date)
            - total_amount: float
            - merchant: string
            - items: list of items with prices
            - payment_method: string
            - delivery_status: string (if applicable)
            """

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )

            receipt_info = json.loads(response.choices[0].message.content)
            
            # Add metadata
            receipt_info.update({
                "processing_timestamp": datetime.utcnow().isoformat(),
                "text_confidence": self._estimate_text_confidence(receipt_text),
                "has_image": True
            })

            return receipt_info

        except Exception as e:
            logger.error(f"Error processing receipt: {str(e)}")
            return self._get_fallback_receipt_info()

    async def validate_evidence(self, 
        evidence: Dict[str, Any], 
        policy: RefundPolicy
    ) -> bool:
        """Validate if evidence meets policy requirements"""
        try:
            # Use GPT-4 to analyze if evidence meets policy requirements
            prompt = f"""
            Determine if this evidence meets the refund policy requirements.

            Evidence:
            {json.dumps(evidence)}

            Policy Requirements:
            Required Evidence: {policy.required_evidence}
            Time Limits: {policy.time_limits}
            Eligibility Criteria: {policy.eligibility_criteria}

            Analyze and respond with JSON:
            {{
                "meets_requirements": boolean,
                "missing_items": list of missing requirements,
                "time_valid": boolean,
                "validation_notes": list of notes
            }}
            """

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )

            validation = json.loads(response.choices[0].message.content)
            
            # Log validation results
            if not validation["meets_requirements"]:
                logger.warning(f"Evidence validation failed: {validation['missing_items']}")
            
            return validation["meets_requirements"]

        except Exception as e:
            logger.error(f"Error validating evidence: {str(e)}")
            return self._basic_validation(evidence, policy)

    def _perform_ocr(self, image_data: bytes) -> str:
        """Perform OCR on receipt image"""
        try:
            # Convert bytes to image
            image = Image.open(io.BytesIO(image_data))
            
            # Perform OCR
            text = pytesseract.image_to_string(image)
            
            return text.strip()
        except Exception as e:
            logger.error(f"OCR failed: {str(e)}")
            return ""

    def _estimate_text_confidence(self, text: str) -> float:
        """Estimate confidence in extracted text"""
        if not text:
            return 0.0
            
        # Basic heuristics for confidence estimation
        indicators = [
            text.count('$'),  # Price indicators
            sum(c.isdigit() for c in text),  # Number of digits
            len([w for w in text.split() if len(w) > 2])  # Word count
        ]
        
        return min(1.0, sum(indicators) / 100)

    def _basic_validation(self, evidence: Dict[str, Any], policy: RefundPolicy) -> bool:
        """Basic validation when GPT-4 validation fails"""
        try:
            # Check if all required evidence types are present
            has_required_fields = all(
                any(req.lower() in str(v).lower() 
                    for v in evidence.values())
                for req in policy.required_evidence
            )
            
            # Check if within time limit
            if 'date' in evidence:
                purchase_date = datetime.fromisoformat(evidence['date'])
                hours_since_purchase = (datetime.utcnow() - purchase_date).total_seconds() / 3600
                within_time_limit = hours_since_purchase <= policy.time_limits.get('standard', float('inf'))
            else:
                within_time_limit = True  # Can't verify time, give benefit of doubt
            
            return has_required_fields and within_time_limit
            
        except Exception as e:
            logger.error(f"Basic validation failed: {str(e)}")
            return False

    def _get_fallback_receipt_info(self) -> Dict[str, Any]:
        """Return fallback receipt information structure"""
        return {
            "order_id": None,
            "date": datetime.utcnow().isoformat(),
            "total_amount": None,
            "merchant": None,
            "items": [],
            "payment_method": None,
            "delivery_status": None,
            "processing_timestamp": datetime.utcnow().isoformat(),
            "text_confidence": 0.0,
            "has_image": False,
            "processing_error": True
        } 