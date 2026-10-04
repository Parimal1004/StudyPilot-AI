"""
SQLAlchemy ORM models for StudyPilot AI.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, Text, JSON, Date,
)
from sqlalchemy.orm import relationship
from backend.database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=True)
    knowledge_level = Column(String(20), nullable=False, default="Beginner")
    daily_study_hours = Column(Float, nullable=False, default=2.0)
    exam_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    subjects = relationship("Subject", back_populates="student", cascade="all, delete-orphan")
    study_sessions = relationship("StudySession", back_populates="student", cascade="all, delete-orphan")
    quiz_results = relationship("QuizResult", back_populates="student", cascade="all, delete-orphan")
    documents = relationship("UploadedDocument", back_populates="student", cascade="all, delete-orphan")


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    name = Column(String(120), nullable=False)
    topics = Column(JSON, default=list)          # list of topic strings
    weak_topics = Column(JSON, default=list)     # list of weak topic strings
    color = Column(String(20), default="#3b82d4")
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="subjects")
    study_sessions = relationship("StudySession", back_populates="subject")
    quiz_results = relationship("QuizResult", back_populates="subject")


class StudySession(Base):
    __tablename__ = "study_sessions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=True)
    date = Column(Date, nullable=False)
    topic = Column(String(200), nullable=False)
    duration_hours = Column(Float, nullable=False, default=1.0)
    activity = Column(String(50), nullable=False, default="Learn")
    # Learn | Practice | Revision | Quiz | Mock Test
    priority = Column(String(20), nullable=False, default="Medium")
    # High | Medium | Low
    objective = Column(Text, nullable=True)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="study_sessions")
    subject = relationship("Subject", back_populates="study_sessions")


class QuizResult(Base):
    __tablename__ = "quiz_results"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=True)
    topic = Column(String(200), nullable=False)
    difficulty = Column(String(20), nullable=False, default="Medium")
    total_questions = Column(Integer, nullable=False)
    correct_answers = Column(Integer, nullable=False, default=0)
    score_percentage = Column(Float, nullable=False, default=0.0)
    weak_areas = Column(JSON, default=list)
    taken_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="quiz_results")
    subject = relationship("Subject", back_populates="quiz_results")


class UploadedDocument(Base):
    __tablename__ = "uploaded_documents"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    filename = Column(String(260), nullable=False)
    original_name = Column(String(260), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size_kb = Column(Float, nullable=True)
    page_count = Column(Integer, nullable=True)
    subject_tag = Column(String(120), nullable=True)
    summary = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="documents")
