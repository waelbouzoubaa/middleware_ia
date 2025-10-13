import os
from typing import List, Dict, Any
from .base import BaseAdapter
from mistralai.client import MistralClient


class MistralAdapter(BaseAdapter):
   

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY") or ""
        if not self.api_key:
            raise RuntimeError("MISTRAL_API_KEY manquante")
        self.client = MistralClient(api_key=self.api_key)

    def send_chat(self, model: str, messages: List[Dict[str, Any]], stream: bool = False):
        """
        Appel simple au modèle Mistral.
        model attendu au format 'mistral:small' -> traduit en 'mistral-small'.
        """
        # Traduction du modèle
        model_id = model.split(":", 1)[1] if ":" in model else model
        model_map = {
            "small": "mistral-small",
            "medium": "mistral-medium",
            "large": "mistral-large"
        }
        model_id = model_map.get(model_id, model_id)

        # Appel API
        response = self.client.chat(model=model_id, messages=messages)

        # Extraction du texte
        content = ""
        try:
            if hasattr(response, "choices") and len(response.choices) > 0:
                msg = response.choices[0].message
                if isinstance(msg, dict):
                    content = msg.get("content", "").strip()
                else:
                    content = getattr(msg, "content", "").strip()
        except Exception as e:
            content = f"(Mistral) Erreur de parsing: {e}"

        # Retour minimal attendu par FastAPI
        return {
            "content": content or "(Mistral) Pas de réponse.",
            "usage": {"input_tokens": 0, "output_tokens": 0},
            "cost_eur": 0.0,
            "est_kwh": 0.0,
            "est_co2e_g": 0.0,
        }
