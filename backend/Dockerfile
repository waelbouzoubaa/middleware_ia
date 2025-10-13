FROM python:3.11-slim

# Outils build + headers (certains wheels en ont besoin)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libffi-dev curl git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Pimper pip et pré-installer les deps
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Code
COPY . /app

EXPOSE 8010
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8010"]
