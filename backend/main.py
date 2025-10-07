import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from typing import List

from models import ChatRequest, ChatResponse, ModelInfo

dotenv_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

from adapters.mock import MockAdapter
from adapters.openrouter_adapter import OpenRouterAdapter  # optionnel
# Mistral
# from adapters.mistral_adapter import MistralAdapter  # importé dynamiquement dans pick_adapter

app = FastAPI(title="Middleware IA - Mistral (direct) + Mock (+OpenRouter optionnel)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODELS: List[ModelInfo] = [
    ModelInfo(provider="mock", model="mock:gpt-mini", label="Mock • GPT Mini", enabled=True),
    # Mistral (direct API)
    ModelInfo(provider="mistral", model="mistral:small", label="Mistral • small-latest", enabled=True),
    ModelInfo(provider="mistral", model="mistral:large", label="Mistral • large-latest", enabled=True),
    ModelInfo(provider="mistral", model="mistral:mixtral", label="Mistral • Mixtral 8x7B (open)", enabled=True),
    # OpenRouter optionnel
    ModelInfo(provider="openrouter", model="openrouter:mistral-nemo", label="OpenRouter • Mistral Nemo (free)", enabled=True),
]

def pick_adapter(model_name: str):
    if model_name.startswith("mistral:"):
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Clé API Mistral absente du .env")
        from adapters.mistral_adapter import MistralAdapter
        return MistralAdapter(api_key)

    if model_name.startswith("openrouter:"):
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Clé API OpenRouter absente du .env")
        return OpenRouterAdapter(api_key)

    if model_name.startswith("mock:"):
        return MockAdapter()

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
