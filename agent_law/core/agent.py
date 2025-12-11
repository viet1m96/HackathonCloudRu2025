from model.tool_decision import ToolDecision
from model.mode_decision import ModeDecision
from core.llm_client import LLMClient
from core.mcp_client import MCPClient
from utils.file_loader import load_file
import requests
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

class Agent:
    def __init__(self, llm_client: LLMClient, mcp_client: MCPClient):
        self.llm_client = llm_client
        self.mcp_client = mcp_client
        self.agent_2_url = os.getenv('API_2_URL') + '/legal-advisor-and-referral'

        self.system_prompt = load_file('./prompt/tool_selector.txt')
        self.mode_selector_prompt = load_file('./prompt/mode_selector.text')

    async def generate(self, user_input: str) -> str:
        tool_decision: ToolDecision = self.llm_client.call(
            user_input, 
            self.system_prompt
        )

        if tool_decision.tool == "none":
            return  {"error": "No suitable MCP tool found."}
        
        summary = await asyncio.to_thread(self.mcp_client.call_tool, tool_decision.tool, tool_decision.arguments)

        mode_input = f"User query: {user_input}\nMCP Summary: {summary}"

        mode_decision: ModeDecision = self.llm_client.call(
            mode_input,
            self.mode_selector_prompt
        )
    
        a2_payload = self.build_agent2_payload(
            user_input=user_input,
            summary=summary,
            mode=mode_decision.mode,
        )

        agent2_result = self.send_to_agent2(a2_payload)

        return {
            "tool": tool_decision.tool,
            "arguments": tool_decision.arguments,
            "summary": summary,
            "agent2_mode": mode_decision.mode,
            "agent2_response": agent2_result
        }

    def build_agent2_payload(self, user_input, summary, mode):
        return {
            "mode": mode,
            "query": user_input,
            "law_context": summary,
            "providers": None,
            "relevant_laws": ""
        }
    
    def send_to_agent2(self, payload: dict) -> dict:
        try:
            headers = {"Content-Type": "application/json"}

            res = requests.post(self.agent_2_url, json=payload, headers=headers)
            res.raise_for_status()
            return res.json()

        except Exception as e:
            return {
                "error": "Failed to contact Agent 2",
                "details": str(e)
            }