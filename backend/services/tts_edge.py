# backend/services/tts_edge.py
from __future__ import annotations
import asyncio
import io
import edge_tts

DEFAULT_VOICE = "ar-MA-MounaNeural"  # بدائل: ar-SA-HamedNeural, ar-SA-ZiyadNeural

async def synthesize_tts(text: str, voice: str | None = None) -> bytes:
    """يحفظ الصوت في بايتات (MP3) ويعيدها."""
    v = voice or DEFAULT_VOICE
    out = io.BytesIO()
    tts = edge_tts.Communicate(text, v)
    async for chunk in tts.stream():
        if chunk["type"] == "audio":
            out.write(chunk["data"])
    return out.getvalue()

def synthesize_tts_sync(text: str, voice: str | None = None) -> bytes:
    """نسخة متزامنة عند الحاجة (لا تُستخدم في FastAPI)."""
    return asyncio.run(synthesize_tts(text, voice))
