"""SQLAlchemy ORM models."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


def _uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Questionnaire(Base):
    __tablename__ = "questionnaires"
    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # pdf, xlsx, txt
    created_at = Column(DateTime, default=datetime.utcnow)
    questions = relationship("Question", back_populates="questionnaire", cascade="all,delete")


class Question(Base):
    __tablename__ = "questions"
    id = Column(String, primary_key=True, default=_uuid)
    questionnaire_id = Column(String, ForeignKey("questionnaires.id"), nullable=False)
    index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    location_meta = Column(String, default="")
    questionnaire = relationship("Questionnaire", back_populates="questions")
    answers = relationship("Answer", back_populates="question", cascade="all,delete")


class Reference(Base):
    __tablename__ = "references"
    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    stored_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    passages = relationship("Passage", back_populates="reference", cascade="all,delete")


class Passage(Base):
    __tablename__ = "passages"
    id = Column(String, primary_key=True, default=_uuid)
    reference_id = Column(String, ForeignKey("references.id"), nullable=False)
    text = Column(Text, nullable=False)
    page_or_para = Column(String, default="")  # "page 2" or "paragraph 5"
    token_count = Column(Integer, default=0)
    embedding_index = Column(Integer, nullable=True)  # position in FAISS index
    reference = relationship("Reference", back_populates="passages")


class Run(Base):
    __tablename__ = "runs"
    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    questionnaire_id = Column(String, ForeignKey("questionnaires.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    answers = relationship("Answer", back_populates="run", cascade="all,delete")


class Answer(Base):
    __tablename__ = "answers"
    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, ForeignKey("runs.id"), nullable=False)
    question_id = Column(String, ForeignKey("questions.id"), nullable=False)
    answer_text = Column(Text, nullable=False)
    citations = Column(Text, default="")  # JSON list of citation strings
    evidence_snippets = Column(Text, default="")  # JSON list of snippet strings
    confidence_score = Column(Integer, default=0)
    is_edited = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    run = relationship("Run", back_populates="answers")
    question = relationship("Question", back_populates="answers")
