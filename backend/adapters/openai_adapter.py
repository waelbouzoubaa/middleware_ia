import os
from typing import List, Dict, Any
from openai import OpenAI
from .base import BaseAdapter
from adapters.carbon_adapter import estimate_carbon


class OpenAIAdapter(BaseAdapter):
    """Adapter pour le fournisseur OpenAI (avec estimation carbone)."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or ""
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY manquante")
        self.client = OpenAI(api_key=self.api_key)

    def send_chat(self, model: str, messages: List[Dict[str, Any]], stream: bool = False):
        """Envoie une requête de chat à l'API OpenAI."""
        model_id = model.split(":", 1)[1] if ":" in model else model

        response = self.client.chat.completions.create(
            model=model_id,
            messages=messages,
            stream=False
        )

        # Contenu du message
        content = ""
        if response and response.choices and response.choices[0].message:
            content = (response.choices[0].message.content or "").strip()

        # Nombre de tokens utilisés
        input_tokens = getattr(response.usage, "prompt_tokens", 0)
        output_tokens = getattr(response.usage, "completion_tokens", 0)

        # Calcul carbone
        carbon_data = estimate_carbon(model, input_tokens, output_tokens)

        return {
            "content": content or "(OpenAI) Pas de contenu renvoyé.",
            "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens},
            "cost_eur": 0.0,
            "est_kwh": round(carbon_data["energy_kwh"], 6),
            "est_co2e_g": round(carbon_data["carbon_gco2eq"], 3),
        }
