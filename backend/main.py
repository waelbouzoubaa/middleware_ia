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
from adapters.openai_adapter import OpenAIAdapter  # optionnel si tu as une clé

app = FastAPI(title="Middleware IA - OpenRouter + Mock (+OpenAI optionnel)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODELS: List[ModelInfo] = [
    ModelInfo(provider="mock", model="mock:gpt-mini", label="Mock • GPT Mini", enabled=True),

    # OpenRouter (free-tier)
    ModelInfo(provider="openrouter", model="openrouter:llama-free", label="OpenRouter • Llama 3.1 8B (free)", enabled=True),
    ModelInfo(provider="openrouter", model="openrouter:phi3-mini", label="OpenRouter • Phi-3 Mini (free)", enabled=True),
    ModelInfo(provider="openrouter", model="openrouter:mistral-nemo", label="OpenRouter • Mistral Nemo (free)", enabled=True),

    # OpenAI (si clé)
    ModelInfo(provider="openai", model="openai:gpt-4o-mini", label="ChatGPT • GPT-4o Mini", enabled=True),
]

def pick_adapter(model_name: str):
    if model_name.startswith("openrouter:"):
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Clé API OpenRouter absente du .env")
        from adapters.openrouter_adapter import OpenRouterAdapter
        return OpenRouterAdapter(api_key)

    if model_name.startswith("openai:"):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Clé API OpenAI absente du .env")
        return OpenAIAdapter(api_key)

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
