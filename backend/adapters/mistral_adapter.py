import os
from typing import List, Dict, Any
from .base import BaseAdapter

# Ecologits (désactivé temporairement)
# from ecologits import EcoLogits   # type: ignore
# EcoLogits.init()

# SDK Mistral (v0.4.x)
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
        model attendu au format 'mistral:small' -> traduit en 'mistral-small' pour l'API.
        """
        model_id = model.split(":", 1)[1] if ":" in model else model

        # 🔧 Correction : mapper vers les vrais noms Mistral
        model_map = {
            "small": "mistral-small",
            "medium": "mistral-medium",
            "large": "mistral-large"
        }
        model_id = model_map.get(model_id, model_id)

        # ✅ Appel à l'API Mistral
        resp = self.client.chat(
            model=model_id,
            messages=messages
        )

        # 🧠 Extraction du contenu texte
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

        # 📊 Tokens
        input_tokens = getattr(resp, "usage", {}).get("prompt_tokens", 0) if hasattr(resp, "usage") else 0
        output_tokens = getattr(resp, "usage", {}).get("completion_tokens", 0) if hasattr(resp, "usage") else 0
        usage = {"input_tokens": input_tokens or 0, "output_tokens": output_tokens or 0}

        # 🌱 Impacts environnementaux (désactivés pour le moment)
        est_kwh = 0.0
        est_co2e_g = 0.0

        return {
            "content": content or "(Mistral) Pas de réponse.",
            "usage": usage,
            "cost_eur": 0.0,
            "est_kwh": est_kwh,
            "est_co2e_g": est_co2e_g,
        }
