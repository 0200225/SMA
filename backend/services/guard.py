# backend/services/guard.py
from __future__ import annotations
import unicodedata, re

ALLOW_HINTS = [
    # عربي عام
    "نبات","نباتات","زرع","زراعة","تربة","ري","سماد","شتلة","شتلات",
    "أصيص","حوض","قصرية","تقليم","تعفن","جذور","أوراق","حصاد","بذور",
    # أمثلة نباتات
    "الطماطم","طماطم","النعناع","نعناع","ريحان","زعتر","خيار","فلفل","باذنجان","ليمون","حمضيات","زيتون",
    # إنجليزي شائع
    "plant","garden","soil","pot","mint","tomato","basil","watering","fertilizer","pruning","compost",
]

REJECT_MSG = (
    "أعتذر، أنا مساعد مختص فقط بالنباتات والزراعة والبستنة. "
    "يرجى صياغة سؤالك ضمن هذا المجال."
)

def _norm(s: str) -> str:
    if not s: return ""
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"[\u064B-\u0652\u0670\u0640]", "", s)  # إزالة الحركات/التطويل
    s = s.replace("أ","ا").replace("إ","ا").replace("آ","ا").replace("ة","ه").replace("ى","ي")
    return re.sub(r"\s+"," ", s).lower().strip()

def in_scope(query: str) -> bool:
    q = _norm(query)
    return any(_norm(k) in q for k in ALLOW_HINTS)

def guard_query(query: str) -> tuple[bool, str | None]:
    return (True, None) if in_scope(query) else (False, REJECT_MSG)
