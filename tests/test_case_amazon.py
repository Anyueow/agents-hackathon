import asyncio
import os
from PIL import Image
import io
import uuid
from pydantic import BaseModel
from agents.refund_agent import RefundAgent
from agents.implementations.policy_fetcher import OpenAIPolicyFetcher
from agents.implementations.openai_message_gen import OpenAIMessageGenerator
from agents.implementations.response_analyzer import OpenAIResponseAnalyzer
from agents.implementations.evidence_processor import OpenAIEvidenceProcessor
import secrets

class RefundContext(BaseModel):
    """Context for the refund workflow"""
    order_id: str | None = None
    order_date: str | None = None
    product_name: str | None = None
    total_amount: float | None = None
    merchant: str | None = None
    payment_method: str | None = None
    delivery_status: str | None = None
    refund_status: str = "pending"
    evidence_processed: bool = False

async def test_amazon_refund():
    """Test refund workflow with actual Amazon order details"""
    
    # Initialize context and AgentOps
    context = RefundContext()
    
    # Generate a conversation ID
    conversation_id = uuid.uuid4().hex[:16]
    
    try:
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
        
        
            
        # Update context with extracted information
        context.order_id = order_details.get('order_id')
        context.order_date = order_details.get('date')
        context.product_name = order_details.get('items', [{}])[0].get('name') if order_details.get('items') else None
        context.total_amount = order_details.get('total_amount')
        context.merchant = order_details.get('merchant')
        context.payment_method = order_details.get('payment_method')
        context.delivery_status = order_details.get('delivery_status')
        context.evidence_processed = True
        
        print("\nExtracted Order Details:")
        print("-" * 20)
        print(f"Order ID: {context.order_id}")
        print(f"Date: {context.order_date}")
        print(f"Product: {context.product_name}")
        print(f"Total Amount: ${context.total_amount}")
        print(f"Merchant: {context.merchant}")
        print(f"Payment Method: {context.payment_method}")
        print(f"Delivery Status: {context.delivery_status}")
        print("-" * 20)

        # Prepare issue description using context
        issue_description = f"""
        Order Details:
        - Order ID: {context.order_id}
        - Date: {context.order_date}
        - Product: {context.product_name}
        - Total Amount: ${context.total_amount}
        - Merchant: {context.merchant}

        Issue Description:
        The product arrived damaged. Upon opening the package, I noticed that the 
        container was cracked, causing some of the product to leak. This makes the 
        product unusable and I would like a refund or replacement.

        Payment Information:
        - Payment Method: {context.payment_method}
        - Delivery Status: {context.delivery_status}
        """

        print("\n2. Initiating refund request...")
        result = await agent.initiate_refund(
            platform="amazon",
            order_id=context.order_id,
            issue_description=issue_description,
            receipt_data=order_image
        )
        
       
        
        print_formatted_result("Initial Request Result:", result)
        context.refund_status = result.get("status", "pending")

        # Test response handling with dynamic order details
        responses = [
            {
                "scenario": "Initial Rejection - Need Photos",
                "response": f"""
                Thank you for contacting Amazon Customer Service.
                I understand you're requesting a refund for the damaged product.
                Could you please provide clear photos of the damage to help us process your claim?
                This will help us better assist you with your refund request for order {context.order_id}.
                """
            },
            {
                "scenario": "Final Approval",
                "response": f"""
                Thank you for your patience. I've reviewed your case and the product details.
                Given that the product arrived damaged, I've approved a full refund of 
                ${context.total_amount} to your {context.payment_method}. 
                You should see this refund in 3-5 business days. You don't need to return the damaged item.
                We apologize for any inconvenience caused.
                """
            }
        ]

        # Process each response scenario
        for scenario in responses:
            print(f"\n{scenario['scenario']}...")
            result = await agent.handle_response(
                order_id=context.order_id,
                response=scenario['response'],
                platform="amazon"
            )
            
            
            
            print_formatted_result(f"{scenario['scenario']} Result:", result)
            context.refund_status = result.get("status", context.refund_status)

       

    except Exception as e:
        # Log error and end workflow with failure
        error_message = str(e)
        print(f"\nError occurred: {error_message}")
        
       
        raise

def print_formatted_result(title, result):
    """Print formatted results with a title"""
    import json
    print(f"\n{title}")
    print("-" * len(title))
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(test_amazon_refund()) 