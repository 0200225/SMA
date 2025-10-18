# ===== Dockerfile في جذر المستودع =====
FROM python:3.11-slim

# نحتاج ffmpeg لـ STT (faster-whisper) + بعض الأدوات الأساسية
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
 && rm -rf /var/lib/apt/lists/*

# مجلد العمل
WORKDIR /app

# ثبّت بايثون باعتماد requirements الخاصة بالباك-إند
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# انسخ كود الباك-إند كله
COPY backend/ /app/

# Render يمرّر منفذ الخدمة عبر متغيّر البيئة PORT
ENV PORT=10000

# شغّل Uvicorn على 0.0.0.0 وبمنفذ $PORT
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
