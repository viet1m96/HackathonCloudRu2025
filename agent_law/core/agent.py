from model.tool_decision import ToolDecision
from core.llm_client import LLMClient
from core.mcp_client import MCPClient
from utils.file_loader import load_file
import asyncio

class Agent:
    def __init__(self, llm_client: LLMClient, mcp_client: MCPClient):
        self.llm_client = llm_client
        self.mcp_client = mcp_client

        self.system_prompt = load_file('./prompt/tool_selector.txt')

    async def generate(self, user_input: str) -> str:
        decision: ToolDecision = self.llm_client.call(user_input, self.system_prompt)

        print(decision)

        if decision.tool == "none":
            return "No suitable MCP tool found."
        
        summary = await asyncio.to_thread(self.mcp_client.call_tool, decision.tool, decision.arguments)

        return {
            "tool": decision.tool,
            "arguments": decision.arguments,
            "summary": summary
        }
    