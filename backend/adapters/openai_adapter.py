from .base import BaseAdapter

class OpenAIAdapter(BaseAdapter):
    """
    Adaptateur simulé pour OpenAI (ChatGPT).
    Pour l'instant, il retourne une réponse fictive pour permettre les tests.
    """

    def __init__(self, api_key=None):
        self.api_key = api_key or "dummy_key"

    def send_chat(self, model: str, messages: list, stream: bool = False):
        prompt = messages[-1]["content"] if messages else ""
        return {
            "content": f"(MOCK) OpenAIAdapter simulé — message reçu : '{prompt[:100]}'",
            "usage": {"input_tokens": 0, "output_tokens": 0},
            "cost_eur": 0.0,
            "est_kwh": 0.0,
            "est_co2e_g": 0.0
        }
