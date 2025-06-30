"""
FastAPI application for LangManus.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Union

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
# from sse_starlette.sse import EventSourceResponse
# import asyncio
# from typing import AsyncGenerator, Dict, List, Any

from src.graph import build_graph
from src.config import TEAM_MEMBERS
from src.service.workflow_service import run_agent_workflow

# Configure logging
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="LangManus API",
    description="API for LangManus LangGraph-based agent workflow",
    version="0.1.0",
)

origins = [
    "http://localhost",
    "http://localhost:3000",
]
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    # allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Create the graph
graph = build_graph()


class ContentItem(BaseModel):
    type: str = Field(..., description="The type of content (text, image, etc.)")
    text: Optional[str] = Field(None, description="The text content if type is 'text'")
    image_url: Optional[str] = Field(
        None, description="The image URL if type is 'image'"
    )


class ChatMessage(BaseModel):
    role: str = Field(
        ..., description="The role of the message sender (user or assistant)"
    )
    content: Union[str, List[ContentItem]] = Field(
        ...,
        description="The content of the message, either a string or a list of content items",
    )


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="The conversation history")
    debug: Optional[bool] = Field(False, description="Whether to enable debug logging")
    deep_thinking_mode: Optional[bool] = Field(
        False, description="Whether to enable deep thinking mode"
    )
    search_before_planning: Optional[bool] = Field(
        False, description="Whether to search before planning"
    )


# @app.post("/api/chat/stream") # origin for merge
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Chat endpoint for LangGraph invoke (non-streaming).
    """
    try:
        # Convert Pydantic models to dictionaries and normalize content format
        logger.debug(f"------------------------------------> chat_endpoint, request={request}")
        messages = []
        for msg in request.messages:
            if isinstance(msg.content, str):
                content = msg.content
            else:
                content = []
                for item in msg.content:
                    if item.type == "text":
                        content.append({"type": "text", "text": item.text})
                    elif item.type == "image":
                        content.append({"type": "image", "image_url": item.image_url})

            messages.append({
                "role": msg.role,
                "content": content
            } if isinstance(content, list) else {
                "role": msg.role,
                "content": content
            })

        result = await run_agent_workflow(
            messages,
            request.debug,
            request.deep_thinking_mode,
            request.search_before_planning,
            # return_final_only=True,
        )

        logger.debug(f"------------------------------------> chat_endpoint, result={result}")
        
        return {"response": result["answer"]}
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred: {str(e)}"
        )