"""
populate_demo.py

Скрипт для наполнения базы демо-пользователями и профилями.
Учитывает, что в models.py используются SQLAlchemy Declarative и SessionLocal.
"""

from random import choice, randint
from hashlib import sha256

from models import Base, engine, SessionLocal, User, Profile

# Наборы данных для случайной генерации
STYLES = ["salsa", "bachata", "kizomba", "swing", "tango"]
LEVELS = ["beginner", "intermediate", "advanced", "pro"]
CITIES = ["Москва", "Санкт-Петербург", "Казань", "Новосибирск"]

def populate_demo():
    # Сбрасываем текущие таблицы
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    session = SessionLocal()
    try:
        for i in range(20):
            username = f"user{i+1}"
            email = f"user{i+1}@example.com"
            city = choice(CITIES)

            # Хешируем пароль "demo123"
            raw_password = "demo123"
            hashed = sha256(raw_password.encode()).hexdigest()

            # Создаем пользователя
            user = User(
                username=username,
                email=email,
                city=city,
                password=hashed,    # сохраняем хеш
                role="user"
            )
            session.add(user)
            session.flush()  # чтобы user.id оказался доступен

            # Генерируем случайный профиль
            main_style = choice(STYLES)
            # Дополнительные стили: две разные случайные строки
            additional = ", ".join({choice(STYLES) for _ in range(2)})
            level = choice(LEVELS)
            age = randint(18, 45)
            gender = choice(["male", "female"])
            preferences = "вечерние занятия"

            profile = Profile(
                user_id=user.id,
                main_style=main_style,
                additional=additional,
                level=level,
                age=age,
                gender=gender,
                preferences=preferences
            )
            session.add(profile)

        session.commit()
        print("БД заполнена демонстрационными данными.")
    except Exception as e:
        session.rollback()
        print("Ошибка при заполнении БД:", e)
    finally:
        session.close()

if __name__ == "__main__":
    populate_demo()
