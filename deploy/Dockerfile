# backend/Dockerfile
FROM python:3.11-slim

# نثبّت FFmpeg (ضروري لـ faster-whisper)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# نثبت باكجات البايثون
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ننسخ الكود
COPY . /app

# Render يمرّر PORT بيئيًا؛ نستعمله
ENV PORT=8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
