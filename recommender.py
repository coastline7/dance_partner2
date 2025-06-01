"""recommender.py

Модуль «Персональный подбор» – интеллектуальные рекомендации.
Использует OpenAI, если доступен; иначе возвращает пустые рекомендации.
"""

from typing import List, Dict
from sqlalchemy.orm import Session

from models import User, Profile, SearchHistory, Feedback
from config import OPENAI_API_KEY, OPENAI_BASE_URL, RECOMMENDATION_LIMIT

# Пытаемся импортировать OpenAI; если не получится, отключаем работу с ним
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

    # Простой stub-класс, чтобы код ниже не падал
    class OpenAI:
        def __init__(self, *args, **kwargs):
            pass

        def chat(self, *args, **kwargs):
            raise RuntimeError("OpenAI не подключён")


# Если OpenAI доступен, инициализируем клиент, иначе создаём stub
client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL) if OPENAI_AVAILABLE else OpenAI()

SYSTEM_PROMPT = (
    "Ты — рекомендательный движок платформы поиска партнёров по танцам.\n"
    "Вход: JSON c полем 'current_user' и списком 'candidates'.\n"
    f"Выбери до {RECOMMENDATION_LIMIT} id кандидатов, наиболее подходящих "
    "по стилю, уровню, городу, предпочтениям и предыдущей обратной связи.\n"
    "Ответ строго JSON-массив чисел."
)


# ─────────────────────────────────────────────────────────── helpers
def _user_json(u: User) -> Dict:
    """Преобразовать пользователя в JSON для отправки в модель."""
    prof = u.profile or Profile()
    return {
        "id": u.id,
        "city": u.city,
        "profile": {
            "main_style": prof.main_style,
            "additional": prof.additional,
            "level": prof.level,
            "age": prof.age,
            "gender": prof.gender,
            "preferences": prof.preferences,
        },
    }


def _history_json(u: User) -> Dict:
    """Преобразовать историю поиска и обратную связь пользователя в JSON."""
    return {
        "search_history": [s.query for s in u.searches[-10:]],
        "feedback": [
            {"partner_id": f.partner_id, "positive": f.positive}
            for f in u.feedback[-30:]
        ]
    }


# ─────────────────────────────────────────────────────────── main
def get_recommendations(db: Session, user_id: int) -> List[int]:
    """
    Вернуть список ID рекомендованных партнёров (отсортировано).
    Если OpenAI недоступен, возвращает пустой список.
    """
    user = db.get(User, user_id)
    if not user or not user.profile:
        return []

    # 1) Формируем пул кандидатов из того же города, кроме самого пользователя
    candidates = (
        db.query(User)
          .join(Profile)
          .filter(User.id != user_id, User.city == user.city)
          .limit(300)
          .all()
    )
    if not candidates:
        return []

    # Если OpenAI не установлен, сразу возвращаем пустое
    if not OPENAI_AVAILABLE:
        return []

    # 2) Собираем полезную информацию для модели
    payload = {
        "current_user": _user_json(user) | _history_json(user),
        "candidates":  [_user_json(c) for c in candidates],
    }

    # 3) Отправляем запрос в OpenAI
    try:
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system",  "content": SYSTEM_PROMPT},
                {"role": "user",    "content": str(payload)}
            ],
            temperature=0.2,
            max_tokens=600
        )
        content = resp.choices[0].message.content
        ids = [int(x) for x in eval(content, {}, {})]
    except Exception as e:
        # Если OpenAI вернул ошибку или неверный формат, возвращаем пустой список
        print("[Recommender] OpenAI error:", e)
        ids = []

    # 4) Фильтруем те ID, которых фактически нет в candidates
    ids = [i for i in ids if any(c.id == i for c in candidates)]
    return ids[:RECOMMENDATION_LIMIT]
