"""
ORM-модели SQLAlchemy → dance_partner.db
"""
from sqlalchemy import (create_engine, Column, Integer, String,
                        Text, Boolean, DateTime, ForeignKey)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
from config import DATABASE_URL

Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class User(Base):
    __tablename__ = "users"
    id       = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    email    = Column(String(120), unique=True, nullable=False)
    city     = Column(String(64), default="")
    password = Column(String(128), nullable=False)
    role     = Column(String(32), default="user")

    profile   = relationship("Profile",      back_populates="user",
                             uselist=False, cascade="all,delete")
    searches  = relationship("SearchHistory",back_populates="user",
                             cascade="all,delete")
    feedback  = relationship("Feedback",     back_populates="user",
                             cascade="all,delete")


class Profile(Base):
    __tablename__ = "profiles"
    id            = Column(Integer, primary_key=True)
    user_id       = Column(Integer, ForeignKey("users.id"))
    main_style    = Column(String(64), default="")
    additional    = Column(String(128), default="")
    level         = Column(String(32),  default="")
    age           = Column(Integer,    default=0)
    gender        = Column(String(16), default="")
    preferences   = Column(Text,       default="")

    user          = relationship("User", back_populates="profile")


class SearchHistory(Base):
    __tablename__ = "search_history"
    id        = Column(Integer, primary_key=True)
    user_id   = Column(Integer, ForeignKey("users.id"))
    query     = Column(String(256))
    city      = Column(String(64))
    style     = Column(String(64))
    level     = Column(String(32))
    timestamp = Column(DateTime, default=datetime.utcnow)

    user      = relationship("User", back_populates="searches")


class Feedback(Base):
    __tablename__ = "feedback"
    id          = Column(Integer, primary_key=True)
    user_id     = Column(Integer, ForeignKey("users.id"))
    partner_id  = Column(Integer)
    positive    = Column(Boolean, default=True)
    timestamp   = Column(DateTime, default=datetime.utcnow)

    user        = relationship("User", back_populates="feedback")


class AggregatedItem(Base):
    __tablename__ = "aggregated_items"
    id         = Column(Integer, primary_key=True)
    module     = Column(String(32))   # "radar" / "social"
    title      = Column(String(300))
    snippet    = Column(String(500))
    source     = Column(String(128))
    link       = Column(String(300), unique=True)
    city       = Column(String(64))
    style      = Column(String(64))
    published  = Column(DateTime, default=datetime.utcnow)

# создаём таблицы при первом запуске
Base.metadata.create_all(engine)
