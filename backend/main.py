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
# جرّب الحارس الخفيف أولاً، ولو رفض نرجع لحارس LLM (يتعامل مع الدارجة)
from services.guard import guard_query as guard_query_static
try:
    from services.guard_llm import guard_query as guard_query_llm
except Exception:
    guard_query_llm = None
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

# ... أعلى الملف كما هو

@app.get("/health")
def health():
    return {"ok": True}

# ✅ دعم HEAD لـ /health (لـ UptimeRobot وغيرها)
@app.head("/health")
def health_head():
    from fastapi import Response
    return Response(status_code=200)

# --------- كتابة → صوت ---------
@app.post("/ask_tts", summary="Ask TTS")
async def ask_tts(payload: AskTTS):
    try:
        q = (payload.query or "").strip()

        ok, msg = guard_query_static(q)
        if not ok and guard_query_llm:
            ok, msg = guard_query_llm(q)

        if not ok:
            audio = await synthesize_tts(msg, payload.voice)
            headers = {"Content-Disposition": f'inline; filename="reject-{uuid.uuid4().hex}.mp3"'}
            return Response(content=audio, media_type="audio/mpeg", headers=headers)

        # ✅ مرّر لغة الواجهة للـLLM
        text = (answer(q, payload.lang) or "").strip()
        if not text:
            text = "لم أتمكن من توليد إجابة الآن."

        try:
            audio = await synthesize_tts(text, payload.voice)
        except Exception:
            print("TTS ERROR:\n", traceback.format_exc())
            safe_text = "حدث خلل مؤقت في خدمة الصوت. خلاصة الإجابة: " + text[:200]
            audio = await synthesize_tts(safe_text, payload.voice)

        headers = {"Content-Disposition": f'inline; filename="reply-{uuid.uuid4().hex}.mp3"'}
        return Response(content=audio, media_type="audio/mpeg", headers=headers)

    except Exception:
        print("FATAL /ask_tts ERROR:\n", traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": "internal_error"})

# --------- صوت → نص → LLM → صوت ---------
@app.post("/ask_voice", summary="Voice → STT → LLM → TTS",
          description="استقبل webm/opus وأعد MP3.")
async def ask_voice(
    audio: UploadFile = File(..., description="ملف webm/opus باسم الحقل audio"),
    lang: str = Form("ar"),
    voice: str = Form("ar-MA-MounaNeural"),
):
    try:
        blob = await audio.read()
        lang_hint = lang.split("-")[0] if "-" in lang else lang
        text_in = (transcribe_webm_bytes(blob, lang_hint=lang_hint) or "").strip()
        if not text_in:
            text_in = "لم أفهم التسجيل الصوتي."

        ok, msg = guard_query_static(text_in)
        if not ok and guard_query_llm:
            ok, msg = guard_query_llm(text_in)
        if not ok:
            mp3 = await synthesize_tts(msg, voice)
            headers = {"Content-Disposition": f'inline; filename="reject-{uuid.uuid4().hex}.mp3"'}
            return Response(content=mp3, media_type="audio/mpeg", headers=headers)

        # ✅ مرّر لغة الواجهة كما هي (مثلاً ar-MA)
        reply = (answer(text_in, lang) or "").strip()
        if not reply:
            reply = "تعذّر توليد إجابة حالياً."

        mp3 = await synthesize_tts(reply, voice)
        headers = {"Content-Disposition": f'inline; filename="reply-{uuid.uuid4().hex}.mp3"'}
        return Response(content=mp3, media_type="audio/mpeg", headers=headers)

    except Exception:
        print("ask_voice ERROR:\n", traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": "ask_voice_failed"})
