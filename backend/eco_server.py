from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="EcoServer", description="Calcul local de l'empreinte carbone IA")


REFERENCE_DATA = {
    "chatgpt-4o": {"energy_wh": 439, "co2_g": 268},
    "mistral-small": {"energy_wh": 22.3, "co2_g": 13.7},
    "llama-3": {"energy_wh": 62.7, "co2_g": 38.3}
}

class FootprintRequest(BaseModel):
    model_name: str
    tokens_used: int

class FootprintResponse(BaseModel):
    model_name: str
    tokens_used: int
    energy_wh: float
    co2_g: float
    equivalent: str


@app.post("/calculate_footprint", response_model=FootprintResponse)
def calculate_footprint(req: FootprintRequest):
    model = req.model_name.lower()
    tokens = req.tokens_used

    if model not in REFERENCE_DATA:
        return {
            "model_name": model,
            "tokens_used": tokens,
            "energy_wh": 0,
            "co2_g": 0,
            "equivalent": "Modèle non reconnu"
        }

    # Calcul proportionnel
    ref = REFERENCE_DATA[model]
    ratio = tokens / 5000
    energy = round(ref["energy_wh"] * ratio, 3)
    co2 = round(ref["co2_g"] * ratio, 3)

    # Conversion en équivalent concret
    equivalent = f"{round(co2 / 13.7 * 12.8, 1)} min de streaming vidéo"

    return {
        "model_name": model,
        "tokens_used": tokens,
        "energy_wh": energy,
        "co2_g": co2,
        "equivalent": equivalent
    }
