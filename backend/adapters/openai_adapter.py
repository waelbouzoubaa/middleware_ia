import os
from typing import List, Dict, Any
from .base import BaseAdapter

# Ecologits doit être initialisé avant usage des SDKs
#from ecologits import EcoLogits   # type: ignore
#EcoLogits.init()

# SDK OpenAI (v1)
from openai import OpenAI


class OpenAIAdapter(BaseAdapter):
    """Adapter OpenAI avec métriques d'impact via Ecologits."""
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or ""
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY manquante")
        # Le SDK v1 s'instancie comme ceci
        self.client = OpenAI(api_key=self.api_key)

    def send_chat(self, model: str, messages: List[Dict[str, Any]], stream: bool = False):
        """
        model attendu au format 'openai:gpt-4o-mini' -> on enlève le prefixe 'openai:'.
        Retourne un dict compatible ChatResponse.
        """
        model_id = model.split(":", 1)[1] if ":" in model else model

        # Appel API (Ecologits a patché le SDK pour joindre impacts sur la réponse)
        resp = self.client.chat.completions.create(
            model=model_id,
            messages=messages,
            stream=False
        )

        # Contenu
        content = ""
        if resp and resp.choices and resp.choices[0].message:
            content = (resp.choices[0].message.content or "").strip()

        # Usage (tokens)
        usage = {
            "input_tokens": getattr(resp.usage, "prompt_tokens", 0) if hasattr(resp, "usage") else 0,
            "output_tokens": getattr(resp.usage, "completion_tokens", 0) if hasattr(resp, "usage") else 0,
        }

        # Impacts Ecologits
        est_kwh = 0.0
        est_co2e_g = 0.0
        if hasattr(resp, "impacts") and resp.impacts:
            # énergie (kWh)
            if hasattr(resp.impacts, "energy") and resp.impacts.energy and hasattr(resp.impacts.energy, "value"):
                est_kwh = float(resp.impacts.energy.value or 0.0)
            # GWP (kgCO2eq) -> convertir en grammes
            if hasattr(resp.impacts, "gwp") and resp.impacts.gwp and hasattr(resp.impacts.gwp, "value"):
                est_co2e_g = float(resp.impacts.gwp.value or 0.0) * 1000.0

        return {
            "content": content or "(OpenAI) Pas de contenu renvoyé.",
            "usage": usage,
            "cost_eur": 0.0,        # tu pourras brancher tes coûts réels ici si tu veux
            "est_kwh": est_kwh,
            "est_co2e_g": est_co2e_g,
        }
