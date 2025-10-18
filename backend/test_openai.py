# test_openai.py
import os
from dotenv import load_dotenv
from openai import OpenAI

from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")


print("MODEL:", os.getenv("OPENAI_MODEL"))
print("KEY starts with:", (os.getenv("OPENAI_API_KEY") or "")[:10])

client = OpenAI()

resp = client.chat.completions.create(
    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    messages=[{"role": "user", "content": "اكتب جملة عربية قصيرة جدًا للتجربة."}],
    max_tokens=30,
    temperature=0.2,
)
print("REPLY:", resp.choices[0].message.content)
