"""
Pydantic schemas for request/response validation in StudyPilot AI.
"""
from __future__ import annotations
from datetime import date, datetime
from typing import Dict, List, Optional, Literal
from pydantic import BaseModel, Field, field_validator, model_validator


# ── Student ────────────────────────────────────────────────────────────────────

class SubjectInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    topics: List[str] = Field(default_factory=list)
    weak_topics: List[str] = Field(default_factory=list)

    @field_validator("topics", "weak_topics", mode="before")
    @classmethod
    def clean_list(cls, v):
        if isinstance(v, str):
            return [t.strip() for t in v.split(",") if t.strip()]
        return [str(t).strip() for t in v if str(t).strip()]


class StudentCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: Optional[str] = Field(None, max_length=200)
    knowledge_level: Literal["Beginner", "Intermediate", "Advanced"] = "Beginner"
    daily_study_hours: float = Field(..., ge=0.5, le=16.0)
    exam_date: date
    subjects: List[SubjectInput] = Field(..., min_length=1)

    @field_validator("exam_date")
    @classmethod
    def exam_date_must_be_future(cls, v):
        if v <= date.today():
            raise ValueError("Exam date must be in the future.")
        return v

    @field_validator("subjects")
    @classmethod
    def subjects_not_empty(cls, v):
        if not v:
            raise ValueError("At least one subject is required.")
        return v


class StudentResponse(BaseModel):
    id: int
    name: str
    email: Optional[str]
    knowledge_level: str
    daily_study_hours: float
    exam_date: date
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Study Session ──────────────────────────────────────────────────────────────

class StudySessionOut(BaseModel):
    id: int
    date: date
    subject_name: Optional[str] = None
    topic: str
    duration_hours: float
    activity: str
    priority: str
    objective: Optional[str]
    is_completed: bool
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class CompleteSessionRequest(BaseModel):
    session_id: int
    notes: Optional[str] = None


# ── Study Plan ─────────────────────────────────────────────────────────────────

class StudyPlanRequest(BaseModel):
    student_id: int


class StudyPlanSessionSchema(BaseModel):
    date: str                    # ISO date string
    subject: str
    topic: str
    duration_hours: float = Field(..., ge=0.25, le=8.0)
    activity: Literal["Learn", "Practice", "Revision", "Quiz", "Mock Test"]
    priority: Literal["High", "Medium", "Low"]
    objective: str


class StudyPlanResponse(BaseModel):
    student_id: int
    total_sessions: int
    sessions: List[StudyPlanSessionSchema]


# ── Quiz ───────────────────────────────────────────────────────────────────────

class QuizRequest(BaseModel):
    student_id: int
    subject: str
    topic: str
    difficulty: Literal["Easy", "Medium", "Hard"] = "Medium"
    num_questions: int = Field(5, ge=1, le=20)


class QuizOption(BaseModel):
    label: str        # "A", "B", "C", "D"
    text: str


class QuizQuestion(BaseModel):
    question_number: int
    question: str
    options: List[QuizOption]
    correct_answer: str    # "A", "B", "C", or "D"
    explanation: str


class QuizResponse(BaseModel):
    quiz_id: str
    subject: str
    topic: str
    difficulty: str
    questions: List[QuizQuestion]


class QuizSubmission(BaseModel):
    student_id: int
    subject: str
    topic: str
    difficulty: str
    answers: Dict[str, str]   # {question_number_str: chosen_label}
    questions: List[QuizQuestion]


class QuizResultOut(BaseModel):
    total_questions: int
    correct_answers: int
    score_percentage: float
    weak_areas: List[str]
    feedback: str
    detailed: List[dict]


# ── AI Tutor ───────────────────────────────────────────────────────────────────

class TutorRequest(BaseModel):
    student_id: int
    question: str = Field(..., min_length=3, max_length=2000)
    explanation_type: Literal[
        "Simple Explanation",
        "Detailed Explanation",
        "Example",
        "Step-by-Step",
    ] = "Simple Explanation"
    subject_context: Optional[str] = None


class TutorResponse(BaseModel):
    answer: str
    explanation_type: str
    knowledge_level: str


# ── PDF / Notes ────────────────────────────────────────────────────────────────

class PDFQuestionRequest(BaseModel):
    student_id: int
    document_id: int
    question: str = Field(..., min_length=3, max_length=1000)


class PDFQuestionResponse(BaseModel):
    answer: str
    document_name: str


class PDFSummaryResponse(BaseModel):
    summary: str
    key_points: List[str]
    document_name: str


# ── Dashboard ──────────────────────────────────────────────────────────────────

class SubjectProgress(BaseModel):
    subject_name: str
    total_sessions: int
    completed_sessions: int
    planned_hours: float
    completed_hours: float
    quiz_avg_score: Optional[float]


class DashboardResponse(BaseModel):
    student_name: str
    knowledge_level: str
    exam_date: date
    days_remaining: int
    total_planned_hours: float
    completed_hours: float
    progress_percentage: float
    total_sessions: int
    completed_sessions: int
    upcoming_sessions: List[StudySessionOut]
    subjects: List[SubjectProgress]
    weak_topics: List[str]
    recent_quiz_scores: List[float]
