# backend/services/stt_local.py
from __future__ import annotations
import os, tempfile, subprocess, uuid
from faster_whisper import WhisperModel

MODEL_NAME = os.getenv("STT_MODEL", "small")
DEVICE     = os.getenv("STT_DEVICE", "cpu")      # "cpu" أو "cuda"
COMPUTE    = os.getenv("STT_COMPUTE", "int8")    # "int8"/"float16"/"int8_float16"...

# تحميل النموذج مرة واحدة
model = WhisperModel(MODEL_NAME, device=DEVICE, compute_type=COMPUTE)

def _to_wav16k(src_path: str) -> str:
    """تحويل أي ملف صوتي إلى WAV أحادي 16kHz عبر FFmpeg."""
    dst = os.path.join(tempfile.gettempdir(), f"stt-{uuid.uuid4().hex}.wav")
    cmd = ["ffmpeg", "-y", "-i", src_path, "-ac", "1", "-ar", "16000", "-f", "wav", dst]
    # لو FFmpeg غير مثبت سيرمي خطأ
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return dst

def transcribe_webm_bytes(b: bytes, lang_hint: str = "ar") -> str:
    """يستقبل Bytes بتنسيق webm/opus من المتصفح ويفرّغه نصيًا."""
    tmp_in = os.path.join(tempfile.gettempdir(), f"u-{uuid.uuid4().hex}.webm")
    with open(tmp_in, "wb") as f:
        f.write(b)

    wav = _to_wav16k(tmp_in)
    segments, info = model.transcribe(wav, language=(lang_hint or "ar"), beam_size=1)
    text = "".join(seg.text for seg in segments).strip()

    try:
        os.remove(tmp_in)
        os.remove(wav)
    except Exception:
        pass

    return text
