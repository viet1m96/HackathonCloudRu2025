from fastapi import APIRouter
from model.user_request import UserRequest
from core.agent import Agent
from core.llm_client import LLMClient
from core.mcp_client import MCPClient

router = APIRouter()

llm_client = LLMClient()
mcp_client = MCPClient()
agent = Agent(llm_client, mcp_client)

@router.post("/user")
async def user_prompt(request: UserRequest):
    return await agent.generate(request.question)