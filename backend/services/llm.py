# backend/services/llm.py
from __future__ import annotations
import os, re, unicodedata
from typing import List
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError, APIError

# حمّل متغيرات البيئة من backend/.env
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
client       = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ========= توجيه صارم: دائماً أجب من منظور النباتات/البستنة/البيئة =========
SYSTEM_PROMPT = (
    "أنت خبير بستنة وزراعة منزلية وبيئة. افهم أسئلة المستخدم سواء كانت بالعربية الفصحى "
    "أو باللهجة المغربية (الدارجة). أجب باختصار شديد (3–6 جمل)، "
    "وبأسلوب مبسّط وواضح. إن كان السؤال بالدارجة المغربية، اسمح لنفسك "
    "باستعمال دارجة خفيفة مفهومة في المغرب، مع مصطلحات زراعية مألوفة، "
    "وإلا فاستعمل فصحى مبسّطة. ركّز على الإرشادات العملية (ري، تربة، سماد، آفات). "
    "تجنّب المقدمات والقوائم الطويلة."
)


FEWSHOT: List[dict] = [
    # مثال 1: فوائد السمسم
    {"role": "user", "content": "ما فوائد السمسم؟"},
    {"role": "assistant", "content":
     "السمسم محصول زيتي متحمل للجفاف نسبيًا ويُفيد في تنويع الدورة الزراعية وتقليل ضغط الآفات على المحاصيل الأخرى."
     " جذوره تُحسّن بنية التربة ويجذب أزهاره الملقِّحات، وتنجح زراعته في تربة جيدة الصرف وري معتدل دون إغراق."
     " لمكافحة المنّ والذبابة البيضاء والعناكب الحمراء استعمل المكافحة المتكاملة: فحص أسبوعي، رش صابون حشري عند اللزوم، والمحافظة على الأعداء الحيوية."
    },
    # مثال 2: سؤال عام بلا كلمات نباتية
    {"role": "user", "content": "ما هي الآفات التي يجب أن أتجنبها؟"},
    {"role": "assistant", "content":
     "في البستنة المنزلية أكثر الآفات شيوعًا المنّ والذبابة البيضاء والعناكب الحمراء وذبابة الفاكهة، إضافة إلى أمراض فطرية كالبياض الدقيقي."
     " قلّل تعرض نباتاتك بالإضاءة والتهوية الجيدة، والريّ المتوازن، وإزالة الأوراق المصابة مبكرًا، واستعمل لاصقات صفراء للفحص."
     " عند الضرورة استخدم صابونًا حشريًا أو زيت النيم دوريًا بتركيز منخفض وتناوب المواد لتجنّب المقاومة."
    },
    # مثال 3: المياه (تأطير بيئي)
    {"role": "user", "content": "حدثني عن المياه."},
    {"role": "assistant", "content":
     "لترشيد مياه الري في الحديقة استخدم الري بالتنقيط وجدولة الري صباحًا، وأضف نشارة عضوية لتقليل التبخر."
     " افحص رطوبة التربة قبل الري وتجنّب السقي السطحي المتكرر لأنه يضعف الجذور."
     " اجمع مياه الأمطار متى أمكن واستعمل حساسات رطوبة أو اختبار الإصبع لضبط الكمية حسب الطقس والتربة."
    },
    {"role":"user", "content":"شحال نسقي النعناع فالصيف؟"},
    {"role":"assistant", "content":
     "فالحر نسقيه قليلاً وبانتظام: دوز عليه مرة كل يومين إلى ثلاثة، "
     "وخلي التربة رطبة ماشي غارقة. دير طبقة نشارة خفيفة فوق التربة باش تحافظ على الرطوبة، "
     "وسقي صباح بكري ولا مع المغرب."},
    {"role":"user", "content":"عندي البياض الدقيقي فالقرعة، شنو ندير؟"},
    {"role":"assistant", "content":
     "قص الأوراق لي فيها إصابة كثيرة، وتهويّة مزيانة للنبات. "
     "نقص السقي على الأوراق وسقي من الجدر. تقدر ترش محلول بيكاربونات خفيف "
     "أو كبريت زراعي بتركيز مناسب مرة فالأسبوع حتى يتحسّن الوضع."}
     


]
# backend/services/llm.py  (أضِفه تحت التعريفات الموجودة)
def normalize_to_msa(text: str) -> str:
    """
    يحوّل اللهجة المغربية/العامية/الفرنسية الممزوجة إلى عربية فصيحة موجزة
    مع الحفاظ على المعنى المتعلق بالبستنة/الزراعة فقط. يرجع جملة أو جملتين كحد أقصى.
    """
    if not text: 
        return ""
    prompt = (
        "حوّل النص التالي (قد يكون بالدارجة المغربية أو عامية أو خليط عربي/فرنسي)"
        " إلى عربية فصحى موجزة مع الحفاظ على المقصود الزراعي/البستني فقط."
        " أعد الناتج كسطر واحد بدون أي شروحات إضافية.\n\n"
        f"النص: {text.strip()}"
    )
    try:
        r = client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=0.1,
            max_tokens=120,
            messages=[
                {"role":"system","content":"محوّل لهجات إلى عربية فصحى موجزة خاصة بالبستنة."},
                {"role":"user","content":prompt},
            ],
        )
        return _cleanup(r.choices[0].message.content or "")
    except Exception:
        return text  # لو حصل خطأ، نرجّع النص كما هو
# ==== Darija normalizer & slot extractor ==================================
import re, unicodedata

def _norm(s: str) -> str:
    s = (s or "").lower().strip()
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"[\u064B-\u0652\u0670\u0640]", "", s)   # حذف الحركات والتطويل
    s = s.replace("أ","ا").replace("إ","ا").replace("آ","ا").replace("ة","ه")
    return re.sub(r"\s+"," ", s)

# دارجة/فرنساعرابي → فصحى (أهم المزروعات الشائعة)
DARija_CROP = {
    "مطيشه": "طماطم", "مطيشة": "طماطم", "طوماط": "طماطم", "tomate": "طماطم",
    "خيزو": "جزر", "زروديه": "جزر", "زرودية": "جزر", "carotte": "جزر",
    "بصله": "بصل", "بصلة": "بصل", "oignon": "بصل",
    "بطاطا": "بطاطس", "patate": "بطاطس", "pomme de terre": "بطاطس",
    "فلفله": "فلفل", "فلفلة": "فلفل", "poivron": "فلفل",
    "بادنجان": "باذنجان", "beringelle": "باذنجان", "aubergine": "باذنجان",
    "قزبر": "كزبرة", "معندس": "بقدونس", "نعناع": "نعناع",
    "قرعه": "كوسة", "كورجيت": "كوسة", "courgette": "كوسة",  # لو قصد اليقطين نعدّله لاحقًا
}

INTENT_KWS = {
    "الزراعة": ["نزرع","زرع","غرس","شتل","كيفاش نغرس","كيف نزرع","طريقة الزراعة"],
    "السقي": ["نسقي","سقي","ري","الماء","اشحال نسقي","متى نسقي"],
    "التسميد": ["نسمد","سماد","تغذية","كمبوست","نيم"],
    "الآفات": ["حشرة","حشرات","دوده","قمل","ذبابة","عنكبوت","مرض","بياض","بقع"],
    "الحصاد": ["نجني","حصد","حصد","وقت الجني"],
}

def extract_slots(text: str):
    t = _norm(text)
    crop = None
    # ابحث عن محصول
    for k,v in DARija_CROP.items():
        if _norm(k) in t:
            crop = v
            break
    # ابحث عن نية السؤال
    intent = None
    for name, kws in INTENT_KWS.items():
        if any(_norm(w) in t for w in kws):
            intent = name
            break
    return crop, intent

def _cleanup(text: str) -> str:
    """فقرة واحدة، بلا مقدمات/تعداد."""
    t = (text or "").strip().strip('"\'')
    t = re.sub(r"^[\-\•\–\—]\s*", "", t, flags=re.MULTILINE)                 # أزل الشرطات
    t = re.sub(r"^(?:بالطبع|حسنًا|حسنا|إليك|فيما يلي|يمكن|يمكنني|عمومًا|عموما|ختامًا)\s*[:\-–—]?\s*", "", t)
    t = re.sub(r"\s*\n+\s*", " ", t)                                         # سطر واحد
    t = re.sub(r"\s{2,}", " ", t)
    return t

def answer(query: str, lang: str = "ar") -> str:
    """
    يجيب دائمًا من منظور البستنة/البيئة، مع تطبيع الدارجة واستخراج (محصول/نية)
    لزيادة الدقة وتقليل التوهان.
    """
    # 1) طَبِّع الدارجة إلى فصحى موجزة
    try:
        q_norm = normalize_to_msa(query)  # من الدالة التي عندنا مسبقًا
    except Exception:
        q_norm = query

    # 2) استخرج المحصول والنية من النص الأصلي (قبل/بعد التطبيع لنزيد الاحتمال)
    crop, intent = extract_slots(query)
    if not crop or not intent:
        c2, i2 = extract_slots(q_norm)
        crop = crop or c2
        intent = intent or i2

    # 3) ابني توجيهًا مقيدًا إن وُجدت سلوتس
    extra = []
    if crop:
        extra.append(f"المحصول المستهدف: {crop}.")
    if intent:
        extra.append(f"نية السؤال: {intent}.")
    extra_text = ("\n" + " ".join(extra)) if extra else ""

    msgs = [
        {"role": "system", "content": SYSTEM_PROMPT + extra_text},
        *FEWSHOT,
        {"role": "user", "content": q_norm.strip() or query.strip()},
    ]

    try:
        r = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=msgs,
            temperature=0.1,
            max_tokens=380,
            top_p=1.0,
        )
        return _cleanup(r.choices[0].message.content or "")
    except RateLimitError:
        return "لا يمكن توليد الإجابة مؤقتًا بسبب حدود الاستخدام، حاول بعد قليل."
    except APIError as e:
        return f"تعذّر التوليد من المزود: {getattr(e,'message',str(e))[:140]}"
    except Exception as e:
        return f"حصل خطأ غير متوقع: {str(e)[:140]}"
