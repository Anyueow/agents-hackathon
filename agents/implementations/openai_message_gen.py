from typing import Dict, Any
from openai import OpenAI
from ..interfaces import IMessageGenerator, RefundPolicy
import json

class OpenAIMessageGenerator(IMessageGenerator):
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    async def generate_request(
        self,
        issue_description: str,
        policy: RefundPolicy,
        order_details: Dict[str, Any]
    ) -> str:
        prompt = f"""
        Generate a professional refund request based on:

        Issue: {issue_description}
        Order Details: {json.dumps(order_details)}
        Platform Policy: {policy.policy_text}
        
        Requirements:
        1. Professional and courteous tone
        2. Reference specific policy points that support the request
        3. Include all relevant order details
        4. Clear statement of desired resolution
        """

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        return response.choices[0].message.content

    async def generate_escalation(
        self,
        previous_response: str,
        policy: RefundPolicy,
        history: list[str]
    ) -> str:
        prompt = f"""
        Generate an escalation message based on:

        Previous Response: {previous_response}
        Platform Policy: {policy.policy_text}
        Conversation History: {json.dumps(history)}
        
        Requirements:
        1. Professional but firm tone
        2. Address specific points from the rejection
        3. Cite relevant policies or consumer rights
        4. Clear escalation request (e.g., supervisor review)
        """

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        return response.choices[0].message.content 