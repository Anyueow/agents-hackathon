from typing import Dict, Any
from openai import OpenAI
import json
from ..interfaces import IResponseAnalyzer, RefundPolicy
from loguru import logger

class OpenAIResponseAnalyzer(IResponseAnalyzer):
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    async def analyze_response(
        self,
        response: str,
        policy: RefundPolicy
    ) -> Dict[str, Any]:
        """
        Analyze platform response to determine status and next steps
        """
        try:
            # Analyze response using GPT-4
            prompt = f"""
            Analyze this response to a refund request and determine:
            1. Whether the refund was approved or denied
            2. If denied, whether escalation is needed
            3. Key points made in the response
            4. Relevant policy violations (if any)
            
            Platform: {policy.platform}
            Response: {response}
            Platform Policy Summary: {policy.policy_text[:500]}
            
            Format the response as JSON with these keys:
            - approved: boolean
            - needs_escalation: boolean
            - key_points: list of main points from response
            - policy_violations: list of violated policies (if any)
            - suggested_action: string (next recommended action)
            - confidence: float (0-1, confidence in analysis)
            """

            gpt_response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3  # Lower temperature for more consistent analysis
            )

            analysis = json.loads(gpt_response.choices[0].message.content)
            
            # Enhance the analysis with additional metadata
            return {
                **analysis,
                "timestamp": self._get_timestamp(),
                "response_length": len(response),
                "analysis_version": "1.0"
            }

        except json.JSONDecodeError:
            logger.error("Error parsing GPT-4 response")
            return self._get_fallback_analysis(response)
        except Exception as e:
            logger.error(f"Error analyzing response: {str(e)}")
            return self._get_fallback_analysis(response)

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat()

    def _get_fallback_analysis(self, response: str) -> Dict[str, Any]:
        """Return fallback analysis when GPT-4 analysis fails"""
        # Use basic keyword matching as fallback
        response_lower = response.lower()
        
        # Simple heuristic analysis
        approved = any(word in response_lower for word in [
            "approved", "accepted", "processed", "refunded"
        ])
        needs_escalation = any(word in response_lower for word in [
            "denied", "rejected", "cannot", "policy", "unfortunately"
        ])

        return {
            "approved": approved,
            "needs_escalation": needs_escalation and not approved,
            "key_points": ["Fallback analysis - basic keyword matching used"],
            "policy_violations": [],
            "suggested_action": "Manual review needed" if not approved else "None needed",
            "confidence": 0.5,
            "timestamp": self._get_timestamp(),
            "response_length": len(response),
            "analysis_version": "1.0-fallback"
        } 