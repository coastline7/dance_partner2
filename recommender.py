"""
Модуль «Персональный подбор» – ChatGPT-рекомендации
"""
from typing import List, Dict
from openai import OpenAI
from sqlalchemy.orm import Session
from models import User, Profile, SearchHistory, Feedback
from config import (OPENAI_API_KEY, OPENAI_BASE_URL,
                    RECOMMENDATION_LIMIT)

client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

SYSTEM_PROMPT = (
    "Ты — рекомендательный движок. "
    f"Нужно выбрать до {RECOMMENDATION_LIMIT} id кандидатов, "
    "наиболее подходящих текущему пользователю по стилю танца, уровню и городу. "
    "Ответ — JSON-массив чисел."
)

# helpers ------------------------------------------------------------------
def _user_json(u: User) -> Dict:
    p = u.profile or Profile()
    return {
        "id": u.id,
        "city": u.city,
        "style": p.main_style,
        "level": p.level,
    }

def _history_json(u: User) -> Dict:
    return {
        "history": [s.query for s in u.searches[-10:]],
        "feedback": [
            {"partner_id": f.partner_id, "positive": f.positive}
            for f in u.feedback[-30:]
        ],
    }

# core ---------------------------------------------------------------------
def get_recommendations(db: Session, user_id: int) -> List[int]:
    user = db.get(User, user_id)
    if not user:
        return []

    candidates = (
        db.query(User)
          .filter(User.id != user_id, User.city == user.city)
          .limit(300)
          .all()
    )
    if not candidates:
        return []

    payload = {
        "current_user": _user_json(user) | _history_json(user),
        "candidates":  [_user_json(c) for c in candidates],
    }

    try:
        rsp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"system","content":SYSTEM_PROMPT},
                      {"role":"user","content":str(payload)}],
            temperature=0.0, max_tokens=200
        )
        ids = [int(x) for x in eval(rsp.choices[0].message.content)]
    except Exception as e:
        print("[Recommender] error:", e)
        ids = []

    valid_ids = {c.id for c in candidates}
    return [i for i in ids if i in valid_ids][:RECOMMENDATION_LIMIT]
