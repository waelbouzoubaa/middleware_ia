import os
from typing import List, Dict, Any
from .base import BaseAdapter
from openai import OpenAI


class OpenAIAdapter(BaseAdapter):
    """Adapter OpenAI (stable, sans Ecologits)."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or ""
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY manquante")
        self.client = OpenAI(api_key=self.api_key)

    def send_chat(self, model: str, messages: List[Dict[str, Any]], stream: bool = False):
        """
        Appel du modèle OpenAI.
        model attendu au format 'openai:gpt-4o-mini' -> 'gpt-4o-mini'.
        """
        model_id = model.split(":", 1)[1] if ":" in model else model

        # Appel API
        resp = self.client.chat.completions.create(
            model=model_id,
            messages=messages,
            stream=False
        )

        # Extraction du texte
        content = ""
        if resp and resp.choices and resp.choices[0].message:
            content = (resp.choices[0].message.content or "").strip()

        # Retour minimal attendu
        return {
            "content": content or "(OpenAI) Pas de contenu renvoyé.",
            "usage": {
                "input_tokens": getattr(resp.usage, "prompt_tokens", 0) if hasattr(resp, "usage") else 0,
                "output_tokens": getattr(resp.usage, "completion_tokens", 0) if hasattr(resp, "usage") else 0,
            },
            "cost_eur": 0.0,
            "est_kwh": 0.0,
            "est_co2e_g": 0.0,
        }
