from typing import Dict, Any, Optional
from .interfaces import (
    IPolicyFetcher,
    IMessageGenerator,
    IResponseAnalyzer,
    IEvidenceProcessor,
    RefundPolicy
)
from loguru import logger

class RefundAgent:
    def __init__(
        self,
        policy_fetcher: IPolicyFetcher,
        message_generator: IMessageGenerator,
        response_analyzer: IResponseAnalyzer,
        evidence_processor: IEvidenceProcessor
    ):
        self.policy_fetcher = policy_fetcher
        self.message_generator = message_generator
        self.response_analyzer = response_analyzer
        self.evidence_processor = evidence_processor
        self.conversation_history: Dict[str, list[str]] = {}

    async def initiate_refund(
        self,
        platform: str,
        order_id: str,
        issue_description: str,
        receipt_data: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """
        Initiate the refund process for a given order
        """
        try:
            # Fetch platform's refund policy
            policy = await self.policy_fetcher.fetch_policy(platform)
            
            # Process receipt if provided
            order_details = {}
            if receipt_data:
                order_details = await self.evidence_processor.process_receipt(receipt_data)
                if not await self.evidence_processor.validate_evidence(order_details, policy):
                    return {
                        "status": "error",
                        "message": "Insufficient evidence for refund request"
                    }

            # Generate initial refund request
            request_message = await self.message_generator.generate_request(
                issue_description=issue_description,
                policy=policy,
                order_details=order_details
            )

            # Store conversation history
            self.conversation_history[order_id] = [request_message]

            return {
                "status": "initiated",
                "message": request_message,
                "tracking_id": order_id
            }

        except Exception as e:
            logger.error(f"Error initiating refund: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to initiate refund: {str(e)}"
            }

    async def handle_response(
        self,
        order_id: str,
        response: str,
        platform: str
    ) -> Dict[str, Any]:
        """
        Handle response from the platform and determine next steps
        """
        try:
            if order_id not in self.conversation_history:
                return {"status": "error", "message": "No active refund request found"}

            policy = await self.policy_fetcher.fetch_policy(platform)
            analysis = await self.response_analyzer.analyze_response(response, policy)

            self.conversation_history[order_id].append(response)

            if analysis.get("approved", False):
                return {
                    "status": "success",
                    "message": "Refund approved",
                    "details": analysis
                }

            if analysis.get("needs_escalation", False):
                escalation_message = await self.message_generator.generate_escalation(
                    previous_response=response,
                    policy=policy,
                    history=self.conversation_history[order_id]
                )
                self.conversation_history[order_id].append(escalation_message)
                return {
                    "status": "escalated",
                    "message": escalation_message,
                    "details": analysis
                }

            return {
                "status": "rejected",
                "message": "Refund request rejected",
                "details": analysis
            }

        except Exception as e:
            logger.error(f"Error handling response: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to process response: {str(e)}"
            } 