import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from typing import List

from models import ChatRequest, ChatResponse, ModelInfo
from adapters.mistral_adapter import MistralAdapter
from adapters.openai_adapter import OpenAIAdapter


#-----------------------------------------------------
from ecologits import EcoLogits

# ✅ Version compatible 0.8.2
EcoLogits.init()  # patch automatique OpenAI + Mistral

import logging

# Configuration du logger pour EcoLogits
logger = logging.getLogger("ecologits")
logger.setLevel(logging.INFO)

# fichier de log
handler = logging.FileHandler("ecologits-traces.jsonl", mode="a", encoding="utf-8")
handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(handler)
#-----------------------------------------------------


# Charger les variables d'environnement
dotenv_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

app = FastAPI(title="Middleware IA - ChatGPT & Mistral")

# Autoriser les requêtes front depuis n'importe quelle origine (pour ta VM)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Liste des modèles affichés dans ton frontend
MODELS: List[ModelInfo] = [
    # --- OpenAI ---
    ModelInfo(provider="openai", model="openai:gpt-4o-mini", label="GPT-4o-Mini", enabled=True),
    ModelInfo(provider="openai", model="openai:gpt-4o", label="GPT-4o", enabled=True),
    ModelInfo(provider="openai", model="openai:gpt-4-turbo", label="GPT-4-Turbo", enabled=True),
    ModelInfo(provider="openai", model="openai:gpt-3.5-turbo", label="GPT-3.5-Turbo", enabled=True),
    ModelInfo(provider="openai", model="openai:gpt-5", label="GPT-5 (bientôt disponible)", enabled=False),

    # --- Mistral (open source uniquement) ---
    ModelInfo(provider="mistral", model="mistral:open-mistral-7b", label="Mistral 7B (Open)", enabled=True),
    ModelInfo(provider="mistral", model="mistral:open-mixtral-8x7b", label="Mixtral 8×7B (Open)", enabled=True),
]

def pick_adapter(model_name: str):
    if model_name.startswith("openai:"):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Clé API OpenAI absente du .env")
        return OpenAIAdapter(api_key)

    if model_name.startswith("mistral:"):
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Clé API Mistral absente du .env")
        return MistralAdapter(api_key)

    raise HTTPException(status_code=404, detail=f"Modèle '{model_name}' non reconnu.")

@app.get("/health")
def health_check():
    return {"status": "ok", "models_supported": len(MODELS)}

@app.get("/models", response_model=List[ModelInfo])
def get_models():
    return [m for m in MODELS if m.enabled]


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    # Vérifie si le modèle est désactivé
    model_info = next((m for m in MODELS if m.model == request.model), None)
    if model_info and not model_info.enabled:
        raise HTTPException(status_code=400, detail=f"Le modèle '{model_info.label}' n’est pas encore disponible.")
    
    adapter = pick_adapter(request.model)
    result = adapter.send_chat(request.model, request.messages)
    return result
