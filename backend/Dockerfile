# Étape 1 : Image de base
FROM python:3.11-slim

# Étape 2 : Répertoire de travail
WORKDIR /app

# Étape 3 : Copier les fichiers nécessaires
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Étape 4 : Copier le reste du code
COPY . .

# Étape 5 : Exposer le port FastAPI
EXPOSE 8010

# Étape 6 : Commande de lancement
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
