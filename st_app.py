# -*- coding: utf-8 -*-
"""
Streamlit-прототип Dance Partner без авторизации, с правильной аналитикой:
• поиск сохраняет запросы в search_history через ORM
• рекомендации показывают случайных пользователей
• агрегация соцсетей
• аналитика строит график по истории гостя
• 7 вкладок (включая 404)
• 2 темы (обычная и для слабовидящих)
"""

import sys
import threading
from typing import Optional

import streamlit as st
from streamlit.web import cli as stcli
from streamlit import runtime

from sqlalchemy.orm import Session

from hashlib import sha256

import pandas as pd  # для построения DataFrame

from models           import SessionLocal, User, Profile, SearchHistory
from recommender      import get_recommendations
from social           import fetch_social
from config           import RECOMMENDATION_LIMIT

# ──────────────────────────────────────────────
#              1.  CSS-THEMES
# ──────────────────────────────────────────────
CSS_BASE = """
<style>
body {background:#f8f9fa;font-family:'Segoe UI',Tahoma,Arial,sans-serif;}
footer {visibility:hidden;}
.header {background:linear-gradient(90deg,#ff7e5f,#feb47b);padding:20px;border-radius:8px;margin-bottom:20px;}
.header h1{color:#fff;margin:0;}
.card{background:#fff;border-radius:10px;padding:20px;margin-bottom:20px;box-shadow:0 4px 8px rgba(0,0,0,0.1);}
.stButton>button{background:#ff7e5f;color:#fff;border:none;border-radius:6px;padding:0.5rem 1rem;font-size:1rem;}
.stButton>button:hover{background:#feb47b;color:#333;}
.stTextInput>div>input,.stSelectbox>div>div>div>div{border:2px solid #ccc;border-radius:6px;padding:0.4rem;font-size:1rem;}
.footer{text-align:center;color:#777;font-size:0.85rem;margin-top:40px;padding:8px;}
</style>
"""

CSS_A11Y = """
<style>
body,div,input,select,textarea,label,h1,h2,h3,h4,h5{background:#000!important;color:#FFD700!important;font-size:18px!important;}
.header{background:#000!important;}
.header h1{color:#FFD700!important;}
.card{background:#000!important;color:#FFD700!important;border:2px solid #FFD700!important;}
.stButton>button{background:#FFD700!important;color:#000!important;border:2px solid #FFD700!important;}
.stTextInput>div>input,.stSelectbox>div>div>div>div{background:#000!important;color:#FFD700!important;border:2px solid #FFD700!important;}
</style>
"""

# ──────────────────────────────────────────────
#       2.  DB & SESSION HELPERS
# ──────────────────────────────────────────────
def db_session() -> Session:
    return SessionLocal()

def current_user() -> Optional[User]:
    return None  # авторизация отключена

# ──────────────────────────────────────────────
#                     3.  PAGES
# ──────────────────────────────────────────────
def card_start():
    st.markdown('<div class="card">', unsafe_allow_html=True)

def card_end():
    st.markdown('</div>', unsafe_allow_html=True)

def page_home():
    card_start()
    st.markdown("## Добро пожаловать в **Dance Partner** ✨")
    st.write("Это приложение работает без авторизации. Найдите партнёра по танцу, просмотрите рекомендации и посты из соцсетей.")
    card_end()

def page_search():
    """
    «Поиск партнёров» сохраняет каждый запрос в таблицу search_history от имени 'guest'.
    """
    card_start()
    st.markdown("### 🔍 Поиск партнёров (запросы сохраняются за гостем)")

    with st.form("search_form"):
        cols = st.columns(4)
        q     = cols[0].text_input("Ключевые слова")
        city  = cols[1].text_input("Город")
        style = cols[2].text_input("Стиль (salsa)")
        level = cols[3].selectbox("Уровень", ["—","beginner","intermediate","advanced","pro"])
        submitted = st.form_submit_button("Выполнить поиск")

    if submitted:
        with db_session() as s:
            # 1) Найти или создать гостя
            guest = s.query(User).filter_by(username="guest").first()
            if not guest:
                hashed = sha256("guest".encode()).hexdigest()
                guest = User(
                    username="guest",
                    email="guest@example.com",
                    city="",
                    password=hashed,
                    role="guest"
                )
                s.add(guest)
                s.flush()
                profile = Profile(
                    user_id=guest.id,
                    main_style="",
                    additional="",
                    level="",
                    age=0,
                    gender="",
                    preferences=""
                )
                s.add(profile)
                s.flush()

            # 2) Сохранить через ORM
            new_search = SearchHistory(
                user_id=guest.id,
                query=q,
                city=city,
                style=style,
                level=level
            )
            s.add(new_search)
            s.commit()

        st.success("🔍 Запрос сохранён в истории (за гостя).")
        st.write(f"Результаты поиска по: **«{q}»**, город: **«{city}»**, стиль: **«{style}»**, уровень: **«{level}»**")
    card_end()

def page_recommend():
    card_start()
    st.markdown("### 🤖 Персональные рекомендации (без авторизации)")
    st.info("Поскольку нет учётки, показываем случайных пользователей из БД.")
    with db_session() as s:
        all_users = s.query(User).filter(User.username != "guest").all()
        if not all_users:
            # создать демо-пользователей при пустой БД
            demo1 = User(username="demo1", email="demo1@example.com", city="Москва",
                         password=sha256("demo".encode()).hexdigest(), role="user")
            demo1.profile = Profile(main_style="salsa", additional="", level="beginner", age=25, gender="male", preferences="")
            demo2 = User(username="demo2", email="demo2@example.com", city="Санкт-Петербург",
                         password=sha256("demo".encode()).hexdigest(), role="user")
            demo2.profile = Profile(main_style="tango", additional="", level="intermediate", age=30, gender="female", preferences="")
            s.add_all([demo1, demo2])
            s.commit()
            all_users = [demo1, demo2]

        import random
        sample = random.sample(all_users, min(RECOMMENDATION_LIMIT, len(all_users)))
        for p in sample:
            prof = p.profile or Profile()
            st.write(f"• **{p.username}** — {prof.main_style or '—'} ({prof.level or '—'}), {p.city}")
    card_end()

def page_social():
    from models import AggregatedItem
    with db_session() as s:
        # ORM-запрос: выбрать первые 20 записей с module='social', сортируя по published DESC
        rows = (
            s.query(AggregatedItem.title, AggregatedItem.source, AggregatedItem.link)
            .filter(AggregatedItem.module == "social")
            .order_by(AggregatedItem.published.desc())
            .limit(20)
            .all()
        )

     if not rows:
         st.info("Постов пока нет. Нажмите «Обновить ленту», чтобы собрать.")
     else:
         for title, source, link in rows:
             st.markdown(f"• **[{source}]** [{title}]({link})")
     card_end()


def page_analytics():
    card_start()
    st.markdown("### 📊 Аналитика по гостевому пользователю 'guest'")
    with db_session() as s:
        guest = s.query(User).filter_by(username="guest").first()
        if not guest:
            st.info("Пока нет данных, выполните хотя бы один поиск, чтобы появилась статистика.")
        else:
            # Получаем все search_history для guest
            history = s.query(SearchHistory).filter(SearchHistory.user_id == guest.id).all()
            if history:
                # Считаем, сколько раз встречается каждый стиль
                stats = {}
                for rec in history:
                    stl = rec.style or "—"
                    stats[stl] = stats.get(stl, 0) + 1

                # Построим DataFrame: две колонки «style» и «count»
                df = pd.DataFrame({
                    "style": list(stats.keys()),
                    "count": list(stats.values())
                })

                # Используем st.bar_chart, передав DataFrame и указав, что индекс — стиль
                df = df.set_index("style")
                st.bar_chart(df["count"])
                st.write("График количества поисков по стилям.")
            else:
                st.info("Гость ещё не сохранил ни одного поиска.")
    card_end()

def page_help():
    card_start()
    st.markdown("### ❓ Справка (FAQ)")
    st.write("**Поиск** — вводите ключевые слова, город, стиль, уровень. Запросы сохраняются за гостем.")
    st.write("**Рекомендации** — отображаем случайных пользователей из БД (не ‘guest’).")
    st.write("**Соцсети** — нажмите «Обновить ленту», чтобы собрать новые посты из VK/Reddit.")
    st.write("**Аналитика** — строится по истории поиска гостя, отображая график по стилям.")
    card_end()

def page_404():
    card_start()
    st.markdown("### 🚫 404 — Страница не найдена")
    st.write("Кажется, вы попали на несуществующий раздел.")
    st.markdown("[← Вернуться на Главную](#)")
    card_end()

# ──────────────────────────────────────────────
#                  4.  MAIN APPLICATION
# ──────────────────────────────────────────────
def main():
    st.set_page_config(page_title="Dance Partner", layout="wide")
    st.markdown(CSS_BASE, unsafe_allow_html=True)

    with st.sidebar:
        if st.checkbox("Тема для слабовидящих"):
            st.markdown(CSS_A11Y, unsafe_allow_html=True)
        st.info("Авторизация отключена. Все запросы сохраняются за гостем.")

    st.markdown('<div class="header"><h1>Dance Partner</h1></div>', unsafe_allow_html=True)

    tabs = st.tabs([
        "🏠 Главная",
        "🔍 Поиск",
        "🤖 Рекомендации",
        "📱 Соцсети",
        "📊 Аналитика",
        "❓ Справка",
        "🚫 404"
    ])

    with tabs[0]:
        page_home()
    with tabs[1]:
        page_search()
    with tabs[2]:
        page_recommend()
    with tabs[3]:
        page_social()
    with tabs[4]:
        page_analytics()
    with tabs[5]:
        page_help()
    with tabs[6]:
        page_404()

    st.markdown('<div class="footer">© 2025 Dance Partner</div>', unsafe_allow_html=True)

# ──────────────────────────────────────────────
#                   5.  ENTRY POINT
# ──────────────────────────────────────────────
if __name__ == "__main__":
    if runtime.exists():
        main()
    else:
        sys.argv = ["streamlit", "run", sys.argv[0]]
        sys.exit(stcli.main())
