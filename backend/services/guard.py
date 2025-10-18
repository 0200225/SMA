from __future__ import annotations
import unicodedata, re

ALLOW_HINTS = [
    "نبات","نباتات","زرع","زراعة","تربة","ري","سماد","شتلة","شتلات","أصيص","قصرية",
    "تقليم","تعفن","جذور","أوراق","حصاد","بذور",
    "الطماطم","طماطم","النعناع","نعناع","ريحان","زعتر","خيار","فلفل","باذنجان","ليمون","حمضيات","زيتون",
    "plant","garden","soil","pot","mint","tomato","basil","watering","fertilizer","pruning","compost",
]

DARIJA_HINTS = [
    "سقي","سقيت","زريعة","غرس","غرسة","شتلة","كمبوست","زبل","حشرة","تربة","رش","ري","فلاحة","بستان",
    "شحال","فين","شنو","عافك","باغي","بزاف","ماشي","واش"
]

REJECT_MSG = (
    "أعتذر، أنا مساعد مختص فقط بالنباتات والزراعة والبستنة والبيئة. "
    "يرجى صياغة سؤالك ضمن هذا المجال."
)

def _norm(s: str) -> str:
    if not s: return ""
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"[\u064B-\u0652\u0670\u0640]", "", s)
    s = s.replace("أ","ا").replace("إ","ا").replace("آ","ا").replace("ة","ه").replace("ى","ي")
    return re.sub(r"\s+"," ", s).lower().strip()

def guard_query(query: str) -> tuple[bool, str | None]:
    q = _norm(query)
    # أي وجود لمفردات زراعية/دارجة ⇒ اسمح
    if any(_norm(k) in q for k in ALLOW_HINTS + DARIJA_HINTS):
        return True, None
    # أي نص عربي حتى لو عام ⇒ اسمح (سنؤطره في الـLLM)
    if re.search(r"[\u0600-\u06FF]", query):
        return True, None
    # غير عربي ولا يوجد مفردات زراعية ⇒ ارفض
    return False, REJECT_MSG
