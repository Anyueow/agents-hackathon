import os
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn
from loguru import logger
import secrets

from agents.refund_agent import RefundAgent
from agents.implementations.openai_message_gen import OpenAIMessageGenerator
# Import other implementations as they're created

# Initialize FastAPI app
app = FastAPI(title="Refund Automation Agent")

# Initialize components
message_generator = OpenAIMessageGenerator(api_key=secrets.OPENAI_API_KEY)
# Initialize other components (policy_fetcher, response_analyzer, evidence_processor)

# Initialize RefundAgent
agent = RefundAgent(
    policy_fetcher=None,  # TODO: Add implementation
    message_generator=message_generator,
    response_analyzer=None,  # TODO: Add implementation
    evidence_processor=None  # TODO: Add implementation
)

class RefundRequest(BaseModel):
    platform: str
    order_id: str
    issue_description: str
    email: Optional[str] = None

@app.post("/process-refund")
async def process_refund(
    platform: str = Form(...),
    order_id: str = Form(...),
    issue_description: str = Form(...),
    receipt: Optional[UploadFile] = File(None),
    email: Optional[str] = Form(None)
):
    try:
        receipt_data = await receipt.read() if receipt else None
        result = await agent.initiate_refund(
            platform=platform,
            order_id=order_id,
            issue_description=issue_description,
            receipt_data=receipt_data
        )
        
        return JSONResponse(
            status_code=200,
            content=result
        )
    except Exception as e:
        logger.error(f"Error processing refund request: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Failed to process refund request"
            }
        )

@app.post("/handle-response/{order_id}")
async def handle_response(
    order_id: str,
    platform: str = Form(...),
    response: str = Form(...)
):
    try:
        result = await agent.handle_response(
            order_id=order_id,
            response=response,
            platform=platform
        )
        return JSONResponse(status_code=200, content=result)
    except Exception as e:
        logger.error(f"Error handling response: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Failed to process response"
            }
        )

def main():
    # Configure logging
    logger.add("data/response_logs/app.log", rotation="500 MB")
    
    # Start the server
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main() 