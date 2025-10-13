import os
from typing import List, Dict, Any
from .base import BaseAdapter

# Ecologits (désactivé temporairement)
# from ecologits import EcoLogits   # type: ignore
# EcoLogits.init()

# SDK Mistral (nouvelle version >= 0.4.0)
from mistralai.client import MistralClient


class MistralAdapter(BaseAdapter):
    """Adapter Mistral pour le middleware IA (compatible SDK 0.4.x)."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY") or ""
        if not self.api_key:
            raise RuntimeError("MISTRAL_API_KEY manquante")
        self.client = MistralClient(api_key=self.api_key)

    def send_chat(self, model: str, messages: List[Dict[str, Any]], stream: bool = False):
        """
        model attendu au format 'mistral:small' -> on enlève le préfixe 'mistral:'.
        """
        model_id = model.split(":", 1)[1] if ":" in model else model

        # Appel API Mistral
        resp = self.client.chat(
            model=model_id,
            messages=messages
        )

        # Contenu du message
        content = ""
        try:
            if hasattr(resp, "choices") and len(resp.choices) > 0:
                message_obj = resp.choices[0].message
                if isinstance(message_obj, dict):
                    content = message_obj.get("content", "").strip()
                else:
                    content = getattr(message_obj, "content", "").strip()
        except Exception:
            content = "(Mistral) Pas de contenu."

        # Usage (tokens)
        input_tokens = getattr(resp, "usage", {}).get("prompt_tokens", 0) if hasattr(resp, "usage") else 0
        output_tokens = getattr(resp, "usage", {}).get("completion_tokens", 0) if hasattr(resp, "usage") else 0
        usage = {"input_tokens": input_tokens or 0, "output_tokens": output_tokens or 0}

        # Estimations (désactivées si Ecologits non installé)
        est_kwh = 0.0
        est_co2e_g = 0.0

        return {
            "content": content or "(Mistral) Pas de réponse.",
            "usage": usage,
            "cost_eur": 0.0,
            "est_kwh": est_kwh,
            "est_co2e_g": est_co2e_g,
        }
