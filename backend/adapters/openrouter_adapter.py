import os
import requests
from .base import BaseAdapter

class OpenRouterAdapter(BaseAdapter):
    """Adapter pour l'API OpenRouter (OpenAI-compatible)."""
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY") or ""
        self.url = "https://openrouter.ai/api/v1/chat/completions"
        self.model_map = {
            "llama-free": "meta-llama/llama-3.1-8b-instruct:free",
            "phi3-mini": "microsoft/phi-3-mini-4k-instruct:free",
            "mistral-nemo": "mistralai/mistral-nemo:free",
        }

    def _resolve_model(self, model: str) -> str:
        try:
            alias = model.split(":", 1)[1].strip()
        except Exception:
            alias = "llama-free"
        return self.model_map.get(alias, alias)

    def send_chat(self, model: str, messages: list, stream: bool = False):
        model_id = self._resolve_model(model)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "Middleware-IA",
        }
        payload = {"model": model_id, "messages": messages, "stream": False}
        try:
            resp = requests.post(self.url, headers=headers, json=payload, timeout=60)
            if resp.status_code != 200:
                return {
                    "content": f"(OpenRouter) {resp.status_code} {resp.reason} — {resp.text[:300]}",
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
                "usage": {"input_tokens": usage.get("prompt_tokens", 0), "output_tokens": usage.get("completion_tokens", 0)},
                "cost_eur": 0.0,
                "est_kwh": 0.0,
                "est_co2e_g": 0.0,
            }
        except Exception as e:
            return {
                "content": f"(OpenRouter) Exception: {e}",
                "usage": {"input_tokens": 0, "output_tokens": 0},
                "cost_eur": 0.0,
                "est_kwh": 0.0,
                "est_co2e_g": 0.0,
            }
