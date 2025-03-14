import asyncio
import os
from agents.refund_agent import RefundAgent
from agents.implementations.policy_fetcher import OpenAIPolicyFetcher
from agents.implementations.openai_message_gen import OpenAIMessageGenerator
from agents.implementations.response_analyzer import OpenAIResponseAnalyzer
from agents.implementations.evidence_processor import OpenAIEvidenceProcessor
import secrets

async def test_refund_workflow():
    """Test the complete refund workflow"""
    
    # Initialize components
    policy_fetcher = OpenAIPolicyFetcher(api_key=secrets.OPENAI_API_KEY)
    message_generator = OpenAIMessageGenerator(api_key=secrets.OPENAI_API_KEY)
    response_analyzer = OpenAIResponseAnalyzer(api_key=secrets.OPENAI_API_KEY)
    evidence_processor = OpenAIEvidenceProcessor(api_key=secrets.OPENAI_API_KEY)

    # Initialize the agent
    agent = RefundAgent(
        policy_fetcher=policy_fetcher,
        message_generator=message_generator,
        response_analyzer=response_analyzer,
        evidence_processor=evidence_processor
    )

    # Real order data from Amazon
    platform = "amazon"
    order_id = "112-0308297-0519429"
    issue_description = """
    I received my order of the Detox Organic Body Scrub but the product appears to be damaged.
    The item was delivered on Wednesday and left near the front door.
    Order details:
    - Order date: March 9, 2025
    - Product: Detox Organic Body Scrub with Himalayan & Sea Salt
    - Price: $25.99
    - Seller: PRESTIGE CONCEPT
    
    I would like a refund or replacement as the product is not in usable condition.
    """

    print("\n1. Initiating refund request...")
    result = await agent.initiate_refund(
        platform=platform,
        order_id=order_id,
        issue_description=issue_description,
        receipt_data=None  # Since we have the order details in the description
    )
    print("\nInitial Request Result:")
    print_formatted_result(result)

    print("\n2. Testing response handling - Rejection Scenario...")
    rejection_response = """
    Thank you for contacting Amazon Customer Service.
    I understand you're requesting a refund for order #112-0308297-0519429.
    Unfortunately, we cannot process your refund at this time as we need more information
    about the damage to the product. Could you please provide photos of the damaged item?
    """

    result = await agent.handle_response(
        order_id=order_id,
        response=rejection_response,
        platform=platform
    )
    print("\nRejection Handling Result:")
    print_formatted_result(result)

    print("\n3. Testing response handling - Approval Scenario...")
    approval_response = """
    Thank you for contacting Amazon Customer Service.
    I've reviewed your case regarding the damaged Detox Organic Body Scrub.
    I'm sorry for the inconvenience. I've processed a full refund of $25.99
    to your Visa card ending in 3066. You should see this refund in 3-5 business days.
    You don't need to return the damaged item.
    """

    result = await agent.handle_response(
        order_id=order_id,
        response=approval_response,
        platform=platform
    )
    print("\nApproval Handling Result:")
    print_formatted_result(result)

def print_formatted_result(result):
    """Print dictionary in a formatted way"""
    import json
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    print("\n=== Starting Refund Automation Test ===")
    asyncio.run(test_refund_workflow())
    print("\n=== Test Complete ===") 