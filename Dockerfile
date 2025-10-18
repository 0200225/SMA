# ---- Dockerfile للـ backend على Render ----
FROM python:3.11-slim

# ffmpeg لازم لـ faster-whisper
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# نزّل المتطلبات أولاً للاستفادة من كاش البناء
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# انسخ كود الباك-إند
COPY backend/ /app/

# تحسين لوجات بايثون
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# شغّل FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
