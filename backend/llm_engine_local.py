from urllib import response

import requests


class LLMEngineLocal:
    def __init__(self, model="qwen3:4b-instruct", base_url="http://localhost:11434"):
        self.model = model
        self.base_url = base_url

    def generate(self, prompt):
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
        )
    
        try:
            data = response.json()
            return data.get("response", "").strip()
        except Exception:
            return response.text.strip()