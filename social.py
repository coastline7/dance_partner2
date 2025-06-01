"""
Модуль «Социальные сети»: VK + Reddit
Сохраняет свежие посты в таблицу AggregatedItem
"""
import logging
from datetime import datetime, timedelta
from typing import List
import praw, vk_api
from sqlalchemy.orm import Session
from models import AggregatedItem
from config import VK_TOKEN, SOCIAL_LIMIT

# Reddit -------------------------------------------------------------------
reddit = praw.Reddit(
    client_id     ="ohMkPHWLrwDFrsRTmjcmbw",
    client_secret ="HJs09L0XUk8M0johwl_WH73TDV7JuQ",
    user_agent    ="DanceSocialBot/1.0",
    ratelimit_seconds=60
)

def _save_reddit(db: Session, kw: str):
    for sub in reddit.subreddit("all").search(kw, sort="new", limit=SOCIAL_LIMIT):
        link = f"https://reddit.com{sub.permalink}"
        if db.query(AggregatedItem).filter_by(link=link).first():
            continue
        db.add(AggregatedItem(
            module   ="social",
            title    = sub.title[:300],
            snippet  = sub.selftext[:500],
            source   = f"reddit/{sub.subreddit}",
            link     = link,
            city     ="",
            style    ="",
            published= datetime.utcfromtimestamp(sub.created_utc)
        ))

# VK -----------------------------------------------------------------------
vk = vk_api.VkApi(token=VK_TOKEN).get_api()

def _save_vk(db: Session, kw: str):
    ts = int((datetime.utcnow() - timedelta(days=7)).timestamp())
    posts = vk.newsfeed.search(q=kw, count=SOCIAL_LIMIT,
                               start_time=ts, v="5.236")
    for it in posts.get("items", []):
        link = f"https://vk.com/wall{it['owner_id']}_{it['id']}"
        if db.query(AggregatedItem).filter_by(link=link).first():
            continue
        txt = (it.get("text") or "").replace("\n", " ")
        db.add(AggregatedItem(
            module   ="social",
            title    = txt[:300],
            snippet  = txt[:500],
            source   ="vk",
            link     = link,
            city     ="",
            style    ="",
            published= datetime.utcfromtimestamp(it["date"])
        ))

# Public API ---------------------------------------------------------------
def fetch_social(db: Session, keywords: List[str]):
    for kw in keywords:
        try:  _save_reddit(db, kw)
        except Exception as e: logging.warning("[Reddit] %s", e)
        try:  _save_vk(db, kw)
        except Exception as e: logging.warning("[VK] %s", e)
    db.commit()
"""Модуль «Социальные сети» – собирает посты из Reddit и VK."""
import logging
from datetime import datetime, timedelta
from typing import List

import praw, vk_api
from sqlalchemy.orm import Session

from models import AggregatedItem
from config import VK_TOKEN, SOCIAL_LIMIT

# ─────────────────────────────────────────────────────────── Reddit
reddit = praw.Reddit(
    client_id="ohMkPHWLrwDFrsRTmjcmbw",
    client_secret="HJs09L0XUk8M0johwl_WH73TDV7JuQ",
    user_agent="DanceSocialBot/1.0",
    ratelimit_seconds=60
)

def _fetch_reddit_keyword(db: Session, kw: str):
    for sub in reddit.subreddit("all").search(kw, sort="new", limit=SOCIAL_LIMIT):
        link = f"https://reddit.com{sub.permalink}"
        if db.query(AggregatedItem).filter_by(link=link).first():
            continue
        db.add(AggregatedItem(
            module   ="social",
            title    = sub.title[:300],
            snippet  = sub.selftext[:500],
            source   = f"reddit/{sub.subreddit}",
            link     = link,
            city     ="",
            style    ="",
            published= datetime.utcfromtimestamp(sub.created_utc)
        ))

# ─────────────────────────────────────────────────────────── VK
vk = vk_api.VkApi(token=VK_TOKEN).get_api()

def _fetch_vk_keyword(db: Session, kw: str):
    start_ts = int((datetime.utcnow() - timedelta(days=7)).timestamp())
    posts = vk.newsfeed.search(q=kw, count=SOCIAL_LIMIT, start_time=start_ts,
                               v="5.236")
    for it in posts.get("items", []):
        link = f"https://vk.com/wall{it['owner_id']}_{it['id']}"
        if db.query(AggregatedItem).filter_by(link=link).first():
            continue
        text = (it.get("text") or "").replace("\n", " ")
        db.add(AggregatedItem(
            module   ="social",
            title    = text[:300],
            snippet  = text[:500],
            source   ="vk",
            link     = link,
            city     ="",
            style    ="",
            published= datetime.utcfromtimestamp(it["date"])
        ))

# ─────────────────────────────────────────────────────────── main
def fetch_reddit(db: Session, keywords: List[str]):
    for kw in keywords:
        try:
            _fetch_reddit_keyword(db, kw.strip())
        except Exception as e:
            logging.warning("[Social] Reddit error: %s", e)
    db.commit()

def fetch_vk(db: Session, keywords: List[str]):
    for kw in keywords:
        try:
            _fetch_vk_keyword(db, kw.strip())
        except Exception as e:
            logging.warning("[Social] VK error: %s", e)
    db.commit()
