import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from typing import List

from models import ChatRequest, ChatResponse, ModelInfo
from adapters.mistral_adapter import MistralAdapter
from adapters.openai_adapter import OpenAIAdapter

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
    ModelInfo(provider="openai", model="openai:gpt-4o-mini", label="ChatGPT (OpenAI)", enabled=True),
    ModelInfo(provider="mistral", model="mistral:small", label="Mistral Small", enabled=True),
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
    adapter = pick_adapter(request.model)
    result = adapter.send_chat(request.model, [m.dict() for m in request.messages])
    return result
