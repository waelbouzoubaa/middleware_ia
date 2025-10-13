import os
import requests
from .base import BaseAdapter

class OpenAIAdapter(BaseAdapter):
    """Adapter pour l'API OpenAI (ChatGPT)."""
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or ""
        self.url = "https://api.openai.com/v1/chat/completions"

    def send_chat(self, model: str, messages: list, stream: bool = False):
        # Extrait l'identifiant du modèle après "openai:"
        model_id = model.split(":", 1)[1].strip() if ":" in model else model
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model_id,
            "messages": messages,
            "stream": False,
        }

        try:
            resp = requests.post(self.url, headers=headers, json=payload, timeout=60)
            if resp.status_code != 200:
                return {
                    "content": f"(OpenAI) {resp.status_code} {resp.reason} — {resp.text[:300]}",
                    "usage": {"input_tokens": 0, "output_tokens": 0},
                    "cost_eur": 0.0,
                    "est_kwh": 0.0,
                    "est_co2e_g": 0.0,
                }

            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = data.get("usage", {}) or {}
            return {
                "content": content or str(data),
                "usage": {
                    "input_tokens": usage.get("prompt_tokens", 0),
                    "output_tokens": usage.get("completion_tokens", 0),
                },
                "cost_eur": 0.0007,
                "est_kwh": 0.002,
                "est_co2e_g": 1.2,
            }
        except Exception as e:
            return {
                "content": f"(OpenAI) Exception: {e}",
                "usage": {"input_tokens": 0, "output_tokens": 0},
                "cost_eur": 0.0,
                "est_kwh": 0.0,
                "est_co2e_g": 0.0,
            }
