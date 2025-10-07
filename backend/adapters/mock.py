from typing import List, Dict, Any
from .base import BaseAdapter

class MockAdapter(BaseAdapter):
    """
    Adaptateur fictif (mock) pour tester le middleware sans coûts ni appels externes.
    """

    def send_chat(self, model: str, messages: List[Dict[str, str]], stream: bool = False) -> Dict[str, Any]:
        # Simule une réponse IA simple
        prompt = messages[-1]["content"] if messages else ""
        fake_response = f"(MOCK) Réponse simulée à : '{prompt[:100]}'"

        # Simule la consommation et les coûts
        usage = {"input_tokens": 32, "output_tokens": 58}
        cost_eur = 0.0001
        est_kwh = 0.00002
        est_co2e_g = 0.005

        return {
            "content": fake_response,
            "usage": usage,
            "cost_eur": cost_eur,
            "est_kwh": est_kwh,
            "est_co2e_g": est_co2e_g
        }
