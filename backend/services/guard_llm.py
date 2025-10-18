# backend/services/guard_llm.py
from __future__ import annotations
import os, json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL  = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

REJECT_MSG = (
    "أعتذر، هذا المساعد مخصّص لأسئلة البيئة والنباتات والبستنة والزراعة المنزلية، "
    "بما يشمل التربة والري والمياه والأسمدة والكمبوست والآفات والأمراض والبذور والمحاصيل، "
    "والاستدامة وإدارة النفايات والتلوث والتنوّع الحيوي وتأثير تغيّر المناخ. "
    "فضلاً أعد صياغة سؤالك ضمن هذا المجال."
)

def guard_query(q: str) -> tuple[bool, str | None]:
    """
    يُصنّف السؤال: داخل/خارج المجال. عند أي خطأ يسمح بالمرور (لا يوقف السلسلة).
    """
    try:
        system = (
            "أنت مصنّف ثنائي. أعِد فقط JSON دون أي نص آخر.\n"
            "اسمح إذا كان السؤال يخص: النباتات، البستنة، الزراعة المنزلية/الحقلية، التربة، الري والمياه، "
            "الأسمدة/الكمبوست، الآفات/الأمراض، البذور والمحاصيل، التقليم والإكثار، "
            "البيئة والاستدامة وإدارة النفايات وإعادة التدوير والتلوث والتنوع الحيوي وتغيّر المناخ وتأثيره على الزراعة، "
            "الحدائق المنزلية والزراعة الحضرية.\n"
            "ارفض إذا كان السؤال عن السياسة، الرياضة، البرمجة العامة، الطب البشري، المال/الأسواق، الترفيه، "
            "أو أي موضوع لا علاقة له بالبيئة أو الزراعة.\n"
            "أعد JSON مثل: {\"allowed\": true, \"why\": \"...\"}"
        )
        r = client.chat.completions.create(
            model=MODEL,
            temperature=0,
            max_tokens=60,
            messages=[
                {"role":"system","content":system},
                {"role":"user","content":q[:600]},
            ],
        )
        raw = (r.choices[0].message.content or "").strip()
        data = json.loads(raw)
        ok = bool(data.get("allowed"))
        return (ok, None if ok else REJECT_MSG)
    except Exception:
        # لا نوقف السلسلة بسبب خطأ في الحارس
        return True, None
