# backend/main.py
from __future__ import annotations
import os, io, uuid, traceback

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel, Field

# خدماتنا
from services.llm import answer
from services.tts_edge import synthesize_tts
from services.guard_llm import guard_query
from services.stt_local import transcribe_webm_bytes


# ✅ تحقّق من المفتاح في backend/.env
if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("ضع مفتاح OPENAI_API_KEY داخل الملف backend/.env")

app = FastAPI(
    title="Smart Garden Assistant – Plants/Agriculture Only",
    version="0.1.0",
)

# ✅ CORS (يمكن تضييقه لاحقاً)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "*",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------- النماذج ---------
class AskTTS(BaseModel):
    query: str = Field(..., description="سؤال المستخدم (نبات/زراعة فقط)")
    lang: str  = Field("ar", description="لغة الإجابة (للنموذج)")
    voice: str = Field("ar-MA-MounaNeural", description="صوت Microsoft Edge TTS")

# --------- نقاط الفحص ---------
@app.get("/")
def root():
    return {"status": "running", "service": "smart-garden-assistant"}

@app.get("/health")
def health():
    return {"ok": True}

# --------- كتابة → صوت ---------
@app.post(
    "/ask_tts",
    summary="Ask TTS",
    description="يدخل نص السؤال {query, lang, voice} ويُرجع ملف MP3 بالصوت.",
)
async def ask_tts(payload: AskTTS):
    try:
        q = (payload.query or "").strip()

        # حارس المجال (نبات/زراعة فقط)
        ok, msg = guard_query(q)
        if not ok:
            # رفض مهذّب بصوت
            audio = await synthesize_tts(msg, payload.voice)
            headers = {"Content-Disposition": f'inline; filename="reject-{uuid.uuid4().hex}.mp3"'}
            return Response(content=audio, media_type="audio/mpeg", headers=headers)

        # إجابة نموذج النص
        text = (answer(q, payload.lang) or "").strip()
        if not text:
            text = "لم أتمكن من توليد إجابة الآن."

        # تحويل الإجابة إلى صوت
        try:
            audio = await synthesize_tts(text, payload.voice)
        except Exception:
            # فشل الصوت → رسالة بديلة
            print("TTS ERROR:\n", traceback.format_exc())
            safe_text = "حدث خلل مؤقت في خدمة الصوت. خلاصة الإجابة: " + text[:200]
            audio = await synthesize_tts(safe_text, payload.voice)

        headers = {"Content-Disposition": f'inline; filename="reply-{uuid.uuid4().hex}.mp3"'}
        return Response(content=audio, media_type="audio/mpeg", headers=headers)

    except Exception:
        print("FATAL /ask_tts ERROR:\n", traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": "internal_error"})

# --------- تسجيل صوتي (WebM/Opus) → نص → إجابة → صوت ---------
# ملاحظة: يتطلّب حزمة python-multipart لكي تعمل UploadFile
# ثبّت: pip install python-multipart
@app.post(
    "/ask_voice",
    summary="Voice → STT → LLM → TTS",
    description="استقبل ملف صوتي (webm/opus) من المتصفح وأعد MP3 بالإجابة.",
)
async def ask_voice(
    audio: UploadFile = File(..., description="ملف webm/opus باسم الحقل audio"),
    lang: str = Form("ar"),
    voice: str = Form("ar-MA-MounaNeural"),
):
    try:
        # 1) STT: تحويل الصوت إلى نص
        blob = await audio.read()
        lang_hint = lang.split("-")[0] if "-" in lang else lang
        text_in = (transcribe_webm_bytes(blob, lang_hint=lang_hint) or "").strip()
        if not text_in:
            text_in = "لم أفهم التسجيل الصوتي."

        # 2) حارس المجال
        ok, msg = guard_query(text_in)
        if not ok:
            mp3 = await synthesize_tts(msg, voice)
            headers = {"Content-Disposition": f'inline; filename="reject-{uuid.uuid4().hex}.mp3"'}
            return Response(content=mp3, media_type="audio/mpeg", headers=headers)

        # 3) LLM: توليد الرد النصي
        reply = (answer(text_in, "ar") or "").strip()
        if not reply:
            reply = "تعذّر توليد إجابة حالياً."

        # 4) TTS: تحويل الرد إلى صوت
        mp3 = await synthesize_tts(reply, voice)
        headers = {"Content-Disposition": f'inline; filename="reply-{uuid.uuid4().hex}.mp3"'}
        return Response(content=mp3, media_type="audio/mpeg", headers=headers)

    except Exception:
        print("ask_voice ERROR:\n", traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": "ask_voice_failed"})
