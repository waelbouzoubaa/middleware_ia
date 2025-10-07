import os
import requests
from .base import BaseAdapter

class MistralAdapter(BaseAdapter):
    """Adapter direct Mistral API (chat/completions, OpenAI-like)."""
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY") or ""
        self.url = "https://api.mistral.ai/v1/chat/completions"
        # Alias simples -> IDs de modèles Mistral
        self.model_map = {
            "small": "mistral-small-latest",
            "large": "mistral-large-latest",
            "nemo": "open-mistral-nemo",
            "mixtral": "open-mixtral-8x7b",
        }

    def _resolve_model(self, model: str) -> str:
        # model format: "mistral:<alias or full id>"
        try:
            alias = model.split(":", 1)[1].strip()
        except Exception:
            alias = "small"
        return self.model_map.get(alias, alias)

    def send_chat(self, model: str, messages: list, stream: bool = False):
        model_id = self._resolve_model(model)
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
                    "content": f"(Mistral) {resp.status_code} {resp.reason} — {resp.text[:300]}",
                    "usage": {"input_tokens": 0, "output_tokens": 0},
                    "cost_eur": 0.0,
                    "est_kwh": 0.0,
                    "est_co2e_g": 0.0,
                }
            data = resp.json()
            # OpenAI-like response
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = data.get("usage", {}) or {}
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            return {
                "content": content or str(data),
                "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens},
                "cost_eur": 0.0,
                "est_kwh": 0.0,
                "est_co2e_g": 0.0,
            }
        except Exception as e:
            return {
                "content": f"(Mistral) Exception: {e}",
                "usage": {"input_tokens": 0, "output_tokens": 0},
                "cost_eur": 0.0,
                "est_kwh": 0.0,
                "est_co2e_g": 0.0,
            }
