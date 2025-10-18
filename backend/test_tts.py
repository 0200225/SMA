import asyncio
import edge_tts

async def main():
    # الجملة التي سيتم تحويلها إلى صوت
    text = "مرحبًا، هذا اختبار لتقنية تحويل النص إلى كلام في مشروع الحديقة الذكية."
    # الصوت باللهجة المغربية (يمكنك تغييره إلى ar-SA-HamedNeural أو ar-SA-ZiyadNeural)
    voice = "ar-MA-MounaNeural"

    tts = edge_tts.Communicate(text, voice)
    await tts.save("tts_test.mp3")
    print("✅ تم إنشاء الملف الصوتي بنجاح: tts_test.mp3")

if __name__ == "__main__":
    asyncio.run(main())
