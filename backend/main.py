import os
import json
import tempfile
import base64
from pathlib import Path
from io import BytesIO
from typing import List

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from PIL import Image

from models import ChatRequest, ChatResponse, ModelInfo
from adapters.mistral_adapter import MistralAdapter
from adapters.openai_adapter import OpenAIAdapter

# -----------------------------------------------------
# 🌱 Tracking empreinte carbone
# -----------------------------------------------------
from ecologits import EcoLogits
import logging

EcoLogits.init(providers=["openai"])
logger = logging.getLogger("ecologits")
logger.setLevel(logging.INFO)
handler = logging.FileHandler("ecologits-traces.jsonl", mode="a", encoding="utf-8")
handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(handler)

# -----------------------------------------------------
# ⚙️ Configuration initiale
# -----------------------------------------------------
dotenv_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

app = FastAPI(title="Middleware IA - Multi-provider (OpenAI, Mistral, Gemini)")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📁 Répertoire d’upload
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# -----------------------------------------------------
# 📦 Liste des modèles
# -----------------------------------------------------
MODELS: List[ModelInfo] = [
    # --- OpenAI ---
    ModelInfo(provider="openai", model="openai:gpt-4o-mini", label="GPT-4o-Mini", enabled=True),
    ModelInfo(provider="openai", model="openai:gpt-4o", label="GPT-4o (Vision)", enabled=True),
    ModelInfo(provider="openai", model="openai:gpt-4-turbo", label="GPT-4-Turbo", enabled=True),
    ModelInfo(provider="openai", model="openai:gpt-3.5-turbo", label="GPT-3.5-Turbo", enabled=True),
    ModelInfo(provider="openai", model="openai:gpt-5", label="GPT-5 (bientôt disponible)", enabled=False),

    # --- Mistral ---
    ModelInfo(provider="mistral", model="mistral:open-mistral-7b", label="Mistral 7B (Open)", enabled=True),
    ModelInfo(provider="mistral", model="mistral:open-mixtral-8x7b", label="Mixtral 8×7B (Open)", enabled=True),
]

# -----------------------------------------------------
# 🧩 Sélection automatique d’adaptateur
# -----------------------------------------------------
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

# -----------------------------------------------------
# 🌡️ Health Check & Liste des modèles
# -----------------------------------------------------
@app.get("/health")
def health_check():
    return {"status": "ok", "models_supported": len(MODELS)}

@app.get("/models", response_model=List[ModelInfo])
def get_models():
    return [m for m in MODELS if m.enabled]

# -----------------------------------------------------
# 💬 Endpoint texte simple
# -----------------------------------------------------
@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    model_info = next((m for m in MODELS if m.model == request.model), None)
    if model_info and not model_info.enabled:
        raise HTTPException(status_code=400, detail=f"Le modèle '{model_info.label}' n’est pas encore disponible.")
    adapter = pick_adapter(request.model)
    result = adapter.send_chat(request.model, request.messages)
    return result

# -----------------------------------------------------
# 📤 Endpoint multiple upload (images / PDF)
# -----------------------------------------------------
@app.post("/chat/upload")
async def chat_upload(files: List[UploadFile] = File(...)):
    """
    Upload multiple de fichiers (images, PDF, etc.)
    Retourne leurs métadonnées (filename, mime, url)
    """
    uploaded_files = []

    for file in files:
        try:
            dest_path = UPLOAD_DIR / file.filename
            with open(dest_path, "wb") as f:
                f.write(await file.read())

            uploaded_files.append({
                "filename": file.filename,
                "mime": file.content_type,
                "url": f"/uploads/{file.filename}"
            })
        except Exception as e:
            uploaded_files.append({
                "filename": file.filename,
                "error": str(e)
            })

    return {"files": uploaded_files}

# -----------------------------------------------------
# 🧠 Endpoint fichier + IA (vision / PDF)
# -----------------------------------------------------
@app.post("/chat/file-to-ai")
async def chat_with_files(
    model: str = Form(...),
    messages: str = Form(...),
    files: List[UploadFile] = File(None)
):
    """
    Combine plusieurs fichiers et envoie au modèle IA (Vision / PDF)
    """
    try:
        messages = json.loads(messages)
    except Exception:
        raise HTTPException(status_code=400, detail="Format JSON invalide pour 'messages'.")

    adapter = pick_adapter(model)

    for file in files or []:
        suffix = Path(file.filename).suffix.lower()
        temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        temp_path.write(await file.read())
        temp_path.close()

        if suffix == ".pdf":
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(temp_path.name)
                text = "".join([page.get_text() for page in doc])
                messages.append({
                    "role": "user",
                    "content": f"Texte extrait du fichier {file.filename} :\n{text[:6000]}..."
                })
                doc.close()
            except Exception as e:
                messages.append({
                    "role": "user",
                    "content": f"[Erreur PDF: {str(e)}]"
                })

        elif suffix in [".jpg", ".jpeg", ".png"]:
            try:
                img = Image.open(temp_path.name)
                buf = BytesIO()
                img.save(buf, format="PNG")
                image_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Image '{file.filename}' envoyée :"},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
                    ]
                })
            except Exception as e:
                messages.append({
                    "role": "user",
                    "content": f"[Erreur image {file.filename} : {str(e)}]"
                })

        os.remove(temp_path.name)

    result = adapter.send_chat(model, messages)
    return result
