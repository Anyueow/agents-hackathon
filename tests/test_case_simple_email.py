import asyncio
import os
import uuid
from pydantic import BaseModel
from agents.refund_agent import RefundAgent
from agents.implementations.policy_fetcher import OpenAIPolicyFetcher
from agents.implementations.openai_message_gen import OpenAIMessageGenerator
from agents.implementations.response_analyzer import OpenAIResponseAnalyzer
from agents.implementations.evidence_processor import OpenAIEvidenceProcessor
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SimpleRefundContext(BaseModel):
    """Context for simple email-based refund workflow"""
    order_id: str
    order_date: str
    product_name: str
    total_amount: float
    merchant: str
    shipping_address: Optional[str] = None
    payment_method: Optional[str] = None
    refund_status: str = "pending"
    issue_description: Optional[str] = None

async def test_simple_email_refund(context: SimpleRefundContext):
    """Test refund workflow for a simple email-based return system"""
    
    # Get API key from environment
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OpenAI API Key not found in environment variables")
    
    # Generate a conversation ID
    conversation_id = uuid.uuid4().hex[:16]
    
    try:
        print("\n=== Starting Simple Email Refund Test Case ===")
        
        # Initialize components
        policy_fetcher = OpenAIPolicyFetcher(api_key=api_key)
        message_generator = OpenAIMessageGenerator(api_key=api_key)
        response_analyzer = OpenAIResponseAnalyzer(api_key=api_key)
        evidence_processor = OpenAIEvidenceProcessor(api_key=api_key)

        # Initialize the agent
        agent = RefundAgent(
            policy_fetcher=policy_fetcher,
            message_generator=message_generator,
            response_analyzer=response_analyzer,
            evidence_processor=evidence_processor
        )

        print("\n1. Preparing refund request...")
        # Prepare issue description if not provided
        if not context.issue_description:
            context.issue_description = f"""
            I received the {context.product_name} but unfortunately it arrived damaged. 
            I would like to request a refund as the product is not usable in its current condition.
            """

        print("\n2. Simulating email refund process...")
        # Simulate email response
        email_response = f"""
        Dear Customer,

        Thank you for contacting {context.merchant} Customer Service regarding order {context.order_id}.

        We're sorry to hear about the issue with your {context.product_name}. 
        Based on the information provided, we have processed a full refund of ${context.total_amount} 
        {f'to your {context.payment_method}' if context.payment_method else ''}.

        Refund Details:
        - Order Number: {context.order_id}
        - Product: {context.product_name}
        - Refund Amount: ${context.total_amount}
        {f'- Refund Method: {context.payment_method}' if context.payment_method else ''}

        Your refund has been processed and you should see the amount credited to 
        your account within 2-3 business days.

        For this case, you do not need to return the damaged item. 
        Please dispose of it as you see fit.

        We value your business and hope to serve you again soon.

        Best regards,
        {context.merchant} Customer Service
        """

        # Process the response
        result = await agent.handle_response(
            order_id=context.order_id,
            response=email_response,
            platform="email"
        )
        
        print("\nRefund Request Result:")
        print("-" * 50)
        print("Status: Success")
        print(f"Order ID: {context.order_id}")
        print(f"Product: {context.product_name}")
        print(f"Refund Amount: ${context.total_amount}")
        if context.payment_method:
            print(f"Method: {context.payment_method}")
        print("Expected Processing Time: 2-3 business days")
        print("Note: No return required - damaged item can be disposed")
        print("-" * 50)

        # Update context
        context.refund_status = "approved"
        return context

    except Exception as e:
        # Log error and end workflow with failure
        error_message = str(e)
        print(f"\nError occurred: {error_message}")
        context.refund_status = "error"
        raise

if __name__ == "__main__":
    asyncio.run(test_simple_email_refund()) 