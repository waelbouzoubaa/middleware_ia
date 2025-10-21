import os
from typing import List, Dict, Any
from mistralai import Mistral
from .base import BaseAdapter
from adapters.carbon_adapter import estimate_carbon


class MistralAdapter(BaseAdapter):
    """Adapter pour le fournisseur Mistral (avec calcul d'empreinte carbone)."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY") or ""
        if not self.api_key:
            raise RuntimeError("MISTRAL_API_KEY manquante")
        self.client = Mistral(api_key=self.api_key)

    def send_chat(self, model: str, messages: List[Dict[str, Any]], stream: bool = False):
        """Envoie une requête de chat à l'API Mistral avec format compatible."""
        model_id = model.split(":", 1)[1] if ":" in model else model

        try:
            # ✅ Conversion 100 % compatible avec l’API Mistral
            formatted_messages = []
            for m in messages:
                if isinstance(m, dict):
                    formatted_messages.append(m)
                elif hasattr(m, "dict"):
                    formatted_messages.append(m.dict())
                else:
                    formatted_messages.append({"role": "user", "content": str(m)})

            response = self.client.chat.complete(
                model=model_id,
                messages=formatted_messages,
            )

            # ✅ Extraction du contenu
            content = ""
            if response and hasattr(response, "choices") and response.choices:
                content = response.choices[0].message.content.strip()

            # ✅ Récupération des tokens
            input_tokens = getattr(response.usage, "prompt_tokens", 0)
            output_tokens = getattr(response.usage, "completion_tokens", 0)

            # ✅ Calcul empreinte carbone
            carbon_data = estimate_carbon(model, input_tokens, output_tokens)

            return {
                "content": content or "(Mistral) Pas de réponse.",
                "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens},
                "cost_eur": 0.0,
                "est_kwh": round(carbon_data["energy_kwh"], 6),
                "est_co2e_g": round(carbon_data["carbon_gco2eq"], 3),
            }

        except Exception as e:
            return {
                "content": f"❌ Erreur Mistral : {str(e)}",
                "usage": {"input_tokens": 0, "output_tokens": 0},
                "cost_eur": 0.0,
                "est_kwh": 0.0,
                "est_co2e_g": 0.0,
            }
