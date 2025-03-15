import streamlit as st
import asyncio
from tests.test_case_simple_email import SimpleRefundContext, test_simple_email_refund
from agents.implementations.evidence_processor import OpenAIEvidenceProcessor
import os
from PIL import Image
import io
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

st.set_page_config(
    page_title="Refund Automation Demo",
    page_icon="🔄",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        margin-top: 1rem;
    }
    .success-message {
        padding: 1rem;
        background-color: #d4edda;
        border-color: #c3e6cb;
        color: #155724;
        border-radius: 0.25rem;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

def get_api_key():
    """Get OpenAI API key from environment or user input"""
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        # Check if API key is in session state
        if 'openai_api_key' not in st.session_state:
            st.session_state.openai_api_key = None
            
        if not st.session_state.openai_api_key:
            st.warning("⚠️ OpenAI API Key not found in environment variables")
            api_key = st.text_input(
                "Enter your OpenAI API Key",
                type="password",
                help="Get your API key from https://platform.openai.com/account/api-keys"
            )
            if api_key:
                st.session_state.openai_api_key = api_key
        else:
            api_key = st.session_state.openai_api_key
            
    return api_key

async def process_image(image_bytes, api_key):
    """Process the uploaded image using OpenAI Evidence Processor"""
    if not api_key:
        raise ValueError("OpenAI API Key is required")
    
    processor = OpenAIEvidenceProcessor(api_key=api_key)
    result = await processor.process_receipt(image_bytes)
    return result

def main():
    st.title("🔄 Refund Automation Demo")
    st.markdown("### Upload your order details and process refund")

    # Get API key
    api_key = get_api_key()
    
    if not api_key:
        st.error("Please provide an OpenAI API key to continue")
        st.stop()

    # Initialize session state
    if 'refund_status' not in st.session_state:
        st.session_state.refund_status = None
        st.session_state.result = None
        st.session_state.order_details = None

    # File uploader
    uploaded_file = st.file_uploader("Upload Order Screenshot", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_file:
        # Display the uploaded image
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Order Screenshot", use_column_width=True)
        
        # Process the image if not already processed
        if not st.session_state.order_details:
            with st.spinner("Processing order details from image..."):
                try:
                    # Convert image to bytes
                    img_byte_arr = io.BytesIO()
                    image.save(img_byte_arr, format=image.format)
                    img_byte_arr = img_byte_arr.getvalue()
                    
                    # Process the image
                    result = asyncio.run(process_image(img_byte_arr, api_key))
                    st.session_state.order_details = result
                except Exception as e:
                    st.error(f"Error processing image: {str(e)}")
                    st.stop()

    # Create two columns for the layout
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Order Details")
        if st.session_state.order_details:
            # Create form for editing extracted details
            with st.form("order_details_form"):
                order_id = st.text_input("Order ID", st.session_state.order_details.get('order_id', ''))
                order_date = st.text_input("Order Date", st.session_state.order_details.get('order_date', ''))
                product_name = st.text_input("Product Name", st.session_state.order_details.get('product_name', ''))
                total_amount = st.number_input("Total Amount", value=float(st.session_state.order_details.get('total_amount', 0)))
                merchant = st.text_input("Merchant", st.session_state.order_details.get('merchant', ''))
                shipping_address = st.text_input("Shipping Address", st.session_state.order_details.get('shipping_address', ''))
                payment_method = st.text_input("Payment Method", st.session_state.order_details.get('payment_method', ''))
                
                submit_button = st.form_submit_button("Confirm Details")
                if submit_button:
                    # Create context with confirmed details
                    st.session_state.context = SimpleRefundContext(
                        order_id=order_id,
                        order_date=order_date,
                        product_name=product_name,
                        total_amount=total_amount,
                        merchant=merchant,
                        shipping_address=shipping_address,
                        payment_method=payment_method
                    )
                    st.success("Order details confirmed!")

    with col2:
        st.subheader("Refund Process")
        
        if hasattr(st.session_state, 'context'):
            # Add a reason for refund
            st.markdown("##### 🔍 Issue Description")
            issue_description = st.text_area(
                "Describe the issue",
                value="The item arrived damaged and is not usable in its current condition.",
                height=100
            )
            
            # Update context with issue description
            st.session_state.context.issue_description = issue_description

            # Add a button to trigger the refund process
            if st.button("Process Refund Request"):
                with st.spinner("Processing refund request..."):
                    try:
                        # Run the async function with context
                        result_context = asyncio.run(test_simple_email_refund(st.session_state.context))
                        st.session_state.refund_status = "success"
                        st.session_state.result = result_context
                    except Exception as e:
                        st.session_state.refund_status = "error"
                        st.session_state.error = str(e)

            # Display results based on refund status
            if st.session_state.refund_status == "success":
                st.success("✅ Refund Successfully Processed!")
                result = st.session_state.result
                st.markdown(f"""
                ##### Refund Details:
                - Status: {result.refund_status.title()}
                - Order ID: {result.order_id}
                - Product: {result.product_name}
                - Amount: ${result.total_amount}
                - Processing Time: 2-3 business days
                - Return Required: No
                - Action Required: None (dispose of damaged item)
                """)
            elif st.session_state.refund_status == "error":
                st.error(f"❌ Error Processing Refund: {st.session_state.error}")
        else:
            st.info("👆 Please confirm order details first")

    # Add footer with additional information
    st.markdown("---")
    st.markdown("""
        ### How it works
        1. Upload your order screenshot
        2. Verify and confirm the extracted order details
        3. Describe the issue with your order
        4. Submit the refund request
        5. Review the automated response and refund status
    """)

if __name__ == "__main__":
    main() 