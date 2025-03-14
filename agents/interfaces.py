from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel

class RefundPolicy(BaseModel):
    platform: str
    policy_text: str
    eligibility_criteria: Dict[str, Any]
    time_limits: Dict[str, int]
    required_evidence: list[str]

class IPolicyFetcher(ABC):
    @abstractmethod
    async def fetch_policy(self, platform: str) -> RefundPolicy:
        """Fetch refund policy for a given platform"""
        pass

class IMessageGenerator(ABC):
    @abstractmethod
    async def generate_request(self, 
        issue_description: str, 
        policy: RefundPolicy,
        order_details: Dict[str, Any]
    ) -> str:
        """Generate refund request message"""
        pass

    @abstractmethod
    async def generate_escalation(self,
        previous_response: str,
        policy: RefundPolicy,
        history: list[str]
    ) -> str:
        """Generate escalation message"""
        pass

class IResponseAnalyzer(ABC):
    @abstractmethod
    async def analyze_response(self, 
        response: str,
        policy: RefundPolicy
    ) -> Dict[str, Any]:
        """Analyze response and determine next steps"""
        pass

class IEvidenceProcessor(ABC):
    @abstractmethod
    async def process_receipt(self, receipt_data: bytes) -> Dict[str, Any]:
        """Process receipt and extract relevant information"""
        pass

    @abstractmethod
    async def validate_evidence(self, 
        evidence: Dict[str, Any], 
        policy: RefundPolicy
    ) -> bool:
        """Validate if evidence meets policy requirements"""
        pass 