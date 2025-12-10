from model.tool_decision import ToolDecision
from core.llm_client import LLMClient
from core.mcp_client import MCPClient
import asyncio

class Agent:
    def __init__(self, llm_client: LLMClient, mcp_client: MCPClient):
        self.llm_client = llm_client
        self.mcp_client = mcp_client

        self.system_prompt = """
        You are an AI assistant. Your job is to choose one MCP tool for the user's request.

        Available tools:
        1. law_lookup(topic: string, country: string)
        2. company_search(industry: string, location: string)
        3. lawyer_finder(specialization: string, country: string)

        Rules:
        - Return JSON only, format: { "tool": "...", "arguments": { ... } }
        - Only select one tool per request
        - If no tool matches, return: { "tool": "none" }        
        
        """

    async def generate(self, user_input: str) -> str:
        decision: ToolDecision = self.llm_client.call(user_input, self.system_prompt)

        if decision.tool == "none":
            return "No suitable MCP tool found."
        
        summary = await asyncio.to_thread(self.mcp_client.call_tool, decision.tool, decision.arguments)

        return {
            "tool": decision.tool,
            "arguments": decision.arguments,
            "summary": summary
        }
    