import os
import requests
from .base import BaseAdapter

class HuggingFaceAdapter(BaseAdapter):
    """
    Adaptateur Hugging Face via Inference API.
    - Mappe des alias (zephyr, falcon, mistral) vers des repos publics.
    - Ajoute X-Wait-For-Model pour réveiller le modèle si endormi.
    - Retourne toujours un objet au format ChatResponse attendu.
    """
    def __init__(self):
        self.api_key = os.getenv("HUGGINGFACE_API_KEY") or "missing"
        # Modèles publics (zephyr est remappé vers un modèle accessible)
        self.model_map = {
            "zephyr": "bigscience/bloom-560m",           # ✅ public & accessible
            "falcon": "tiiuae/falcon-7b-instruct",       # peut être restreint
            "mistral": "mistralai/Mistral-7B-Instruct-v0.2",  # souvent restreint
        }

    def _resolve_repo(self, model_name: str) -> str:
        # model_name format: "huggingface:<alias>"
        try:
            alias = model_name.split(":", 1)[1].strip().lower()
        except Exception:
            alias = "zephyr"
        return self.model_map.get(alias, self.model_map["zephyr"])

    def send_chat(self, model: str, messages, stream: bool = False):
        repo = self._resolve_repo(model)
        url = f"https://api-inference.huggingface.co/models/{repo}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-Wait-For-Model": "true",  # réveille le modèle si endormi
        }
        prompt = messages[-1]["content"] if messages else ""

        try:
            resp = requests.post(url, headers=headers, json={"inputs": prompt}, timeout=90)
            if resp.status_code == 200:
                data = resp.json()
                text = ""
                if isinstance(data, list) and data and isinstance(data[0], dict):
                    text = data[0].get("generated_text") or data[0].get("generated_texts") or ""
                else:
                    text = str(data)

                return {
                    "content": text or "(HF) Réponse vide",
                    "usage": {"input_tokens": 0, "output_tokens": 0},
                    "cost_eur": 0.0,
                    "est_kwh": 0.0,
                    "est_co2e_g": 0.0,
                }
            else:
                return {
                    "content": f"(HF) {resp.status_code} {resp.reason} pour {repo} — corps: {resp.text[:300]}",
                    "usage": {"input_tokens": 0, "output_tokens": 0},
                    "cost_eur": 0.0,
                    "est_kwh": 0.0,
                    "est_co2e_g": 0.0,
                }
        except Exception as e:
            return {
                "content": f"(HF) Exception: {e}",
                "usage": {"input_tokens": 0, "output_tokens": 0},
                "cost_eur": 0.0,
                "est_kwh": 0.0,
                "est_co2e_g": 0.0,
            }
