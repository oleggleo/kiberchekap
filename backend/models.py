from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text

from db import Base

EMBEDDING_DIM = 768


def utcnow():
    return datetime.now(timezone.utc)


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    phone = Column(String(30), nullable=False)
    email = Column(String(200), nullable=False)
    inn = Column(String(12), nullable=True)
    segment = Column(String(120), nullable=True)
    cyber_problem = Column(String(300), nullable=True)
    okved_code = Column(String(12), nullable=True)
    okved_name = Column(String(400), nullable=True)
    okved_score = Column(Float, nullable=True)
    status = Column(String(20), default="new", nullable=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    auto_active = Column(Boolean, default=False, nullable=False)
    next_send_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, index=True, nullable=False)
    event = Column(String(60), nullable=False)
    subject = Column(String(300))
    status = Column(String(20), default="sent", nullable=False)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class Reply(Base):
    __tablename__ = "replies"

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, index=True, nullable=False)
    from_email = Column(String(200))
    subject = Column(String(300))
    body = Column(Text)
    message_id = Column(String(300), unique=True)
    received_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    login = Column(String(80), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    role = Column(String(20), default="manager", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class Okved(Base):
    __tablename__ = "okved"

    code = Column(String(12), primary_key=True)
    name = Column(String(400), nullable=False)
    embedding = Column(Vector(EMBEDDING_DIM), nullable=False)
