import requests
import os
from dotenv import load_dotenv

load_dotenv()

class MCPClient:
    def __init__(self):
        self.base_url = os.getenv("MCP_BASE_URL")  
        self.headers = {"Content-Type": "application/json"}

    def call_tool(self, tool: str, arguments: dict) -> str:
        url = f"{self.base_url}/{tool}" 
        try:
            response = requests.post(url, json=arguments, headers=self.headers)
            response.raise_for_status()
            return response.text  
        except requests.exceptions.RequestException as e:
            print(f"MCP call failed: {e}")
            return f"MCP call failed for tool {tool}"
