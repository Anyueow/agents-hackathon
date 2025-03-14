import asyncio
import os
from PIL import Image
import io
from agents.refund_agent import RefundAgent
from agents.implementations.policy_fetcher import OpenAIPolicyFetcher
from agents.implementations.openai_message_gen import OpenAIMessageGenerator
from agents.implementations.response_analyzer import OpenAIResponseAnalyzer
from agents.implementations.evidence_processor import OpenAIEvidenceProcessor
import secrets

async def test_amazon_refund():
    """Test refund workflow with actual Amazon order details"""
    
    print("\n=== Starting Amazon Refund Test Case ===")
    
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

    # Load the screenshot as evidence
    screenshot_path = os.path.join("tests", "test_data", "amazon_order.png")
    with open(screenshot_path, 'rb') as f:
        order_image = f.read()

    print("\n1. Processing order evidence...")
    # Extract order details from the image using evidence processor
    order_details = await evidence_processor.process_receipt(order_image)
    
    print("\nExtracted Order Details:")
    print("-" * 20)
    print(f"Order ID: {order_details.get('order_id', 'Not found')}")
    print(f"Date: {order_details.get('date', 'Not found')}")
    print(f"Items: {order_details.get('items', 'Not found')}")
    print(f"Total Amount: ${order_details.get('total_amount', 'Not found')}")
    print(f"Merchant: {order_details.get('merchant', 'Not found')}")
    print(f"Payment Method: {order_details.get('payment_method', 'Not found')}")
    print(f"Delivery Status: {order_details.get('delivery_status', 'Not found')}")
    print("-" * 20)

    # Prepare issue description using extracted details
    issue_description = f"""
    Order Details:
    - Order ID: {order_details.get('order_id')}
    - Date: {order_details.get('date')}
    - Items: {', '.join(str(item) for item in order_details.get('items', []))}
    - Total Amount: ${order_details.get('total_amount')}
    - Merchant: {order_details.get('merchant')}

    Issue Description:
    The product arrived damaged. Upon opening the package, I noticed that the 
    container was cracked, causing some of the product to leak. This makes the 
    product unusable and I would like a refund or replacement.

    Payment Information:
    - Payment Method: {order_details.get('payment_method')}
    - Delivery Status: {order_details.get('delivery_status')}
    """

    print("\n2. Initiating refund request...")
    result = await agent.initiate_refund(
        platform="amazon",
        order_id=order_details.get('order_id'),
        issue_description=issue_description,
        receipt_data=order_image
    )
    print_formatted_result("Initial Request Result:", result)

    # Test response handling with dynamic order details
    responses = [
        {
            "scenario": "Initial Rejection - Need Photos",
            "response": f"""
            Thank you for contacting Amazon Customer Service.
            I understand you're requesting a refund for the damaged product.
            Could you please provide clear photos of the damage to help us process your claim?
            This will help us better assist you with your refund request for order {order_details.get('order_id')}.
            """
        },
        {
            "scenario": "Final Approval",
            "response": f"""
            Thank you for your patience. I've reviewed your case and the product details.
            Given that the product arrived damaged, I've approved a full refund of 
            ${order_details.get('total_amount')} to your {order_details.get('payment_method')}. 
            You should see this refund in 3-5 business days. You don't need to return the damaged item.
            We apologize for any inconvenience caused.
            """
        }
    ]

    # Process each response scenario
    for scenario in responses:
        print(f"\n{scenario['scenario']}...")
        result = await agent.handle_response(
            order_id=order_details.get('order_id'),
            response=scenario['response'],
            platform="amazon"
        )
        print_formatted_result(f"{scenario['scenario']} Result:", result)

def print_formatted_result(title, result):
    """Print formatted results with a title"""
    import json
    print(f"\n{title}")
    print("-" * len(title))
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(test_amazon_refund()) 