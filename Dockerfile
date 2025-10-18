# ---------- Dockerfile (backend on Render) ----------
FROM python:3.11-slim

# ffmpeg مطلوب لـ faster-whisper
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# نزّل المتطلبات أولاً (من backend/ لأننا في الجذر)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# انسخ كود الباك-إند فقط
COPY backend /app

# شغّل Uvicorn على المنفذ الذي تعطيه Render (مهم جدًا!)
ENV PYTHONUNBUFFERED=1
CMD ["sh","-c","uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
