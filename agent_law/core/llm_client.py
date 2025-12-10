from dotenv import load_dotenv
import os
import requests
from model.tool_decision import ToolDecision

load_dotenv()

class LLMClient():
    def __init__(self):
        self.api_key = os.getenv("API_KEY")
        self.base_url = os.getenv("BASE_URL") + "/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def call(self, user_input: str, system_prompt: str) -> ToolDecision:
        payload = {
            "model": "ai-sage/GigaChat3-10B-A1.8B",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 300,
            "frequency_penalty": 0.5,
            "presence_penalty": 0.3,
            "structure_output": True 
        }

        response = requests.post(self.base_url, headers=self.headers, json=payload)

        print(response)

    
        try:
            response = requests.post(self.base_url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return ToolDecision.model_validate_json(content)

        except requests.exceptions.HTTPError as http_err:
            if response.status_code == 402:
                print("LLM API 402: Payment Required or out of credits")
                return ToolDecision(tool="none", arguments={})
            else:
                raise http_err

        except requests.exceptions.RequestException as req_err:
            print(f"LLM Request Error: {req_err}")
            return ToolDecision(tool="none", arguments={})

        except ValueError as val_err:
            print(f"LLM JSON Error: {val_err}")
            return ToolDecision(tool="none", arguments={})
