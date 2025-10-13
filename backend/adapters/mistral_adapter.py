import os
from typing import List, Dict, Any
from .base import BaseAdapter

# Ecologits (doit être init avant import/usage du SDK)
from ecologits import EcoLogits   # type: ignore
EcoLogits.init()

# SDK Mistral
from mistralai import Mistral


class MistralAdapter(BaseAdapter):
    """Adapter Mistral avec métriques d'impact via Ecologits."""
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY") or ""
        if not self.api_key:
            raise RuntimeError("MISTRAL_API_KEY manquante")
        self.client = Mistral(api_key=self.api_key)

    def send_chat(self, model: str, messages: List[Dict[str, Any]], stream: bool = False):
        """
        model attendu au format 'mistral:small' -> on enlève le prefixe 'mistral:'.
        """
        model_id = model.split(":", 1)[1] if ":" in model else model

        # Mistral SDK – API chat
        resp = self.client.chat.complete(
            model=model_id,
            messages=messages,
        )

        # Texte
        content = ""
        try:
            content = resp.choices[0].message["content"].strip()
        except Exception:
            content = str(getattr(resp, "output_text", "")) or "(Mistral) Pas de contenu."

        # Usage tokens (dispo sur certaines versions du SDK)
        input_tokens = getattr(getattr(resp, "usage", None), "prompt_tokens", 0)
        output_tokens = getattr(getattr(resp, "usage", None), "completion_tokens", 0)
        usage = {"input_tokens": input_tokens or 0, "output_tokens": output_tokens or 0}

        # Impacts Ecologits
        est_kwh = 0.0
        est_co2e_g = 0.0
        if hasattr(resp, "impacts") and resp.impacts:
            if hasattr(resp.impacts, "energy") and resp.impacts.energy and hasattr(resp.impacts.energy, "value"):
                est_kwh = float(resp.impacts.energy.value or 0.0)
            if hasattr(resp.impacts, "gwp") and resp.impacts.gwp and hasattr(resp.impacts.gwp, "value"):
                est_co2e_g = float(resp.impacts.gwp.value or 0.0) * 1000.0

        return {
            "content": content,
            "usage": usage,
            "cost_eur": 0.0,
            "est_kwh": est_kwh,
            "est_co2e_g": est_co2e_g,
        }
