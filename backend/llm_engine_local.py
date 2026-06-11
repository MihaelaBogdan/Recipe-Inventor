import requests


class LLMEngineLocal:
    def __init__(self, model="qwen3:4b-instruct", base_url="http://localhost:11434"):
        self.model = model
        self.base_url = base_url

    def generate(self, prompt: str, temperature=0.7, max_tokens=300):

        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }

        response = requests.post(url, json=payload, timeout=60)

        if response.status_code != 200:
            raise Exception(f"Ollama error: {response.text}")

        return response.json().get("response", "").strip()