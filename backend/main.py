"""
StudyPilot AI — FastAPI Backend
Run with: uvicorn backend.main:app --reload --port 8000
"""
import logging
import os
import sys
from datetime import date, datetime
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, UploadFile, File, Form, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

load_dotenv()

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import get_db, init_db
from backend import models
from backend import schemas
from backend import planner, quiz, tutor, pdf_processor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="StudyPilot AI",
    description="AI-powered personal study assistant for college students.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    init_db()
    logger.info("StudyPilot AI backend started. Database initialised.")


# ── Health ─────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "service": "StudyPilot AI"}


# ── Students ───────────────────────────────────────────────────────────────────

@app.post("/students", response_model=schemas.StudentResponse, status_code=201, tags=["Students"])
def create_student(payload: schemas.StudentCreate, db: Session = Depends(get_db)):
    """Create a new student profile with subjects."""
    # Check for duplicate name (simple dedup)
    existing = (
        db.query(models.Student)
        .filter(models.Student.name == payload.name)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A student named '{payload.name}' already exists. "
                   "Please use a unique name or update the existing profile.",
        )

    student = models.Student(
        name=payload.name,
        email=payload.email,
        knowledge_level=payload.knowledge_level,
        daily_study_hours=payload.daily_study_hours,
        exam_date=payload.exam_date,
    )
    db.add(student)
    db.flush()  # get student.id without committing

    for subj_in in payload.subjects:
        subject = models.Subject(
            student_id=student.id,
            name=subj_in.name,
            topics=subj_in.topics,
            weak_topics=subj_in.weak_topics,
        )
        db.add(subject)

    db.commit()
    db.refresh(student)
    logger.info("Created student: %s (id=%d)", student.name, student.id)
    return student


@app.get("/students", response_model=List[schemas.StudentResponse], tags=["Students"])
def list_students(db: Session = Depends(get_db)):
    return db.query(models.Student).order_by(models.Student.created_at.desc()).all()


@app.get("/students/{student_id}", response_model=schemas.StudentResponse, tags=["Students"])
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")
    return student


@app.delete("/students/{student_id}", tags=["Students"])
def delete_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")
    db.delete(student)
    db.commit()
    return {"detail": "Student deleted successfully."}


# ── Study Plan ─────────────────────────────────────────────────────────────────

@app.post("/study-plan/generate", response_model=schemas.StudyPlanResponse, tags=["Study Plan"])
def generate_plan(payload: schemas.StudyPlanRequest, db: Session = Depends(get_db)):
    """Generate (or regenerate) a personalised AI study plan."""
    student = db.query(models.Student).filter(models.Student.id == payload.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    if not student.subjects:
        raise HTTPException(
            status_code=400,
            detail="No subjects found for this student. Please add subjects first.",
        )

    days_remaining = (student.exam_date - date.today()).days
    if days_remaining <= 0:
        raise HTTPException(
            status_code=400,
            detail="The exam date has already passed. Please update your profile.",
        )

    try:
        sessions = planner.generate_study_plan(student, db)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return schemas.StudyPlanResponse(
        student_id=student.id,
        total_sessions=len(sessions),
        sessions=sessions,
    )


@app.get("/study-plan/{student_id}", response_model=List[schemas.StudySessionOut], tags=["Study Plan"])
def get_study_plan(student_id: int, db: Session = Depends(get_db)):
    """Retrieve all planned study sessions for a student."""
    sessions = (
        db.query(models.StudySession)
        .filter(models.StudySession.student_id == student_id)
        .order_by(models.StudySession.date, models.StudySession.id)
        .all()
    )
    result = []
    for s in sessions:
        result.append(
            schemas.StudySessionOut(
                id=s.id,
                date=s.date,
                subject_name=s.subject.name if s.subject else None,
                topic=s.topic,
                duration_hours=s.duration_hours,
                activity=s.activity,
                priority=s.priority,
                objective=s.objective,
                is_completed=s.is_completed,
                completed_at=s.completed_at,
            )
        )
    return result


@app.post("/study-plan/complete-session", tags=["Study Plan"])
def complete_session(payload: schemas.CompleteSessionRequest, db: Session = Depends(get_db)):
    """Mark a study session as completed."""
    session = db.query(models.StudySession).filter(
        models.StudySession.id == payload.session_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Study session not found.")
    if session.is_completed:
        raise HTTPException(status_code=400, detail="Session is already marked as completed.")

    session.is_completed = True
    session.completed_at = datetime.utcnow()
    session.notes = payload.notes
    db.commit()
    return {"detail": "Session marked as completed.", "session_id": session.id}


# ── Dashboard ──────────────────────────────────────────────────────────────────

@app.get("/dashboard/{student_id}", response_model=schemas.DashboardResponse, tags=["Dashboard"])
def get_dashboard(student_id: int, db: Session = Depends(get_db)):
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    today = date.today()
    days_remaining = max(0, (student.exam_date - today).days)

    all_sessions = (
        db.query(models.StudySession)
        .filter(models.StudySession.student_id == student_id)
        .all()
    )
    completed_sessions = [s for s in all_sessions if s.is_completed]
    total_planned_hours = sum(s.duration_hours for s in all_sessions)
    completed_hours = sum(s.duration_hours for s in completed_sessions)
    progress_pct = (
        round((completed_hours / total_planned_hours) * 100, 1)
        if total_planned_hours > 0
        else 0.0
    )

    # Upcoming sessions (today + future, not completed, up to 10)
    upcoming_raw = [
        s for s in all_sessions if not s.is_completed and s.date >= today
    ]
    upcoming_raw.sort(key=lambda s: (s.date, s.priority == "Low", s.priority == "Medium"))
    upcoming_sessions = [
        schemas.StudySessionOut(
            id=s.id,
            date=s.date,
            subject_name=s.subject.name if s.subject else None,
            topic=s.topic,
            duration_hours=s.duration_hours,
            activity=s.activity,
            priority=s.priority,
            objective=s.objective,
            is_completed=s.is_completed,
            completed_at=s.completed_at,
        )
        for s in upcoming_raw[:10]
    ]

    # Subject-level progress
    subject_progress: List[schemas.SubjectProgress] = []
    for subj in student.subjects:
        subj_sessions = [s for s in all_sessions if s.subject_id == subj.id]
        subj_completed = [s for s in subj_sessions if s.is_completed]
        subj_quiz_results = (
            db.query(models.QuizResult)
            .filter(
                models.QuizResult.student_id == student_id,
                models.QuizResult.subject_id == subj.id,
            )
            .all()
        )
        avg_score = (
            round(
                sum(r.score_percentage for r in subj_quiz_results) / len(subj_quiz_results),
                1,
            )
            if subj_quiz_results
            else None
        )
        subject_progress.append(
            schemas.SubjectProgress(
                subject_name=subj.name,
                total_sessions=len(subj_sessions),
                completed_sessions=len(subj_completed),
                planned_hours=sum(s.duration_hours for s in subj_sessions),
                completed_hours=sum(s.duration_hours for s in subj_completed),
                quiz_avg_score=avg_score,
            )
        )

    # Weak topics (from subjects)
    all_weak = []
    for subj in student.subjects:
        all_weak.extend(subj.weak_topics or [])

    # Recent quiz scores
    recent_quizzes = (
        db.query(models.QuizResult)
        .filter(models.QuizResult.student_id == student_id)
        .order_by(models.QuizResult.taken_at.desc())
        .limit(10)
        .all()
    )
    recent_scores = [r.score_percentage for r in recent_quizzes]

    return schemas.DashboardResponse(
        student_name=student.name,
        knowledge_level=student.knowledge_level,
        exam_date=student.exam_date,
        days_remaining=days_remaining,
        total_planned_hours=round(total_planned_hours, 1),
        completed_hours=round(completed_hours, 1),
        progress_percentage=progress_pct,
        total_sessions=len(all_sessions),
        completed_sessions=len(completed_sessions),
        upcoming_sessions=upcoming_sessions,
        subjects=subject_progress,
        weak_topics=list(set(all_weak)),
        recent_quiz_scores=recent_scores,
    )


# ── Quiz ───────────────────────────────────────────────────────────────────────

@app.post("/quiz/generate", response_model=schemas.QuizResponse, tags=["Quiz"])
def generate_quiz_endpoint(payload: schemas.QuizRequest, db: Session = Depends(get_db)):
    """Generate an AI-powered MCQ quiz."""
    student = db.query(models.Student).filter(models.Student.id == payload.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    try:
        questions = quiz.generate_quiz(
            subject=payload.subject,
            topic=payload.topic,
            difficulty=payload.difficulty,
            num_questions=payload.num_questions,
            knowledge_level=student.knowledge_level,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    import uuid as _uuid
    return schemas.QuizResponse(
        quiz_id=str(_uuid.uuid4()),
        subject=payload.subject,
        topic=payload.topic,
        difficulty=payload.difficulty,
        questions=questions,
    )


@app.post("/quiz/submit", response_model=schemas.QuizResultOut, tags=["Quiz"])
def submit_quiz(payload: schemas.QuizSubmission, db: Session = Depends(get_db)):
    """Submit quiz answers and get scored results."""
    student = db.query(models.Student).filter(models.Student.id == payload.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    try:
        result = quiz.score_quiz(payload, payload.student_id, db)
    except Exception as e:
        logger.error("Quiz scoring error: %s", e)
        raise HTTPException(status_code=500, detail="An error occurred while scoring the quiz.")

    return result


@app.get("/quiz/history/{student_id}", tags=["Quiz"])
def get_quiz_history(student_id: int, db: Session = Depends(get_db)):
    """Get all quiz results for a student."""
    results = (
        db.query(models.QuizResult)
        .filter(models.QuizResult.student_id == student_id)
        .order_by(models.QuizResult.taken_at.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "subject_id": r.subject_id,
            "topic": r.topic,
            "difficulty": r.difficulty,
            "total_questions": r.total_questions,
            "correct_answers": r.correct_answers,
            "score_percentage": r.score_percentage,
            "weak_areas": r.weak_areas,
            "taken_at": r.taken_at.isoformat(),
        }
        for r in results
    ]


# ── AI Tutor ───────────────────────────────────────────────────────────────────

@app.post("/tutor/ask", response_model=schemas.TutorResponse, tags=["Tutor"])
def ask_tutor(payload: schemas.TutorRequest, db: Session = Depends(get_db)):
    """Ask the AI tutor a study question."""
    student = db.query(models.Student).filter(models.Student.id == payload.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    try:
        answer = tutor.answer_question(
            question=payload.question,
            explanation_type=payload.explanation_type,
            knowledge_level=student.knowledge_level,
            subject_context=payload.subject_context,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return schemas.TutorResponse(
        answer=answer,
        explanation_type=payload.explanation_type,
        knowledge_level=student.knowledge_level,
    )


# ── PDF / Notes ────────────────────────────────────────────────────────────────

@app.post("/notes/upload", tags=["Notes"])
async def upload_pdf(
    student_id: int = Form(...),
    subject_tag: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a PDF document for a student."""
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_bytes = await file.read()

    try:
        saved_name, file_path = pdf_processor.save_uploaded_pdf(file_bytes, file.filename)
        text, page_count = pdf_processor.extract_text(file_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e))

    doc = models.UploadedDocument(
        student_id=student_id,
        filename=saved_name,
        original_name=file.filename,
        file_path=file_path,
        file_size_kb=round(len(file_bytes) / 1024, 1),
        page_count=page_count,
        subject_tag=subject_tag,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {
        "document_id": doc.id,
        "original_name": doc.original_name,
        "page_count": page_count,
        "file_size_kb": doc.file_size_kb,
        "message": "PDF uploaded and processed successfully.",
    }


@app.get("/notes/{student_id}", tags=["Notes"])
def list_documents(student_id: int, db: Session = Depends(get_db)):
    docs = (
        db.query(models.UploadedDocument)
        .filter(models.UploadedDocument.student_id == student_id)
        .order_by(models.UploadedDocument.uploaded_at.desc())
        .all()
    )
    return [
        {
            "id": d.id,
            "original_name": d.original_name,
            "page_count": d.page_count,
            "file_size_kb": d.file_size_kb,
            "subject_tag": d.subject_tag,
            "uploaded_at": d.uploaded_at.isoformat(),
            "has_summary": d.summary is not None,
        }
        for d in docs
    ]


@app.post("/notes/ask", response_model=schemas.PDFQuestionResponse, tags=["Notes"])
def ask_about_pdf(payload: schemas.PDFQuestionRequest, db: Session = Depends(get_db)):
    """Ask a question about an uploaded PDF document."""
    doc = db.query(models.UploadedDocument).filter(
        models.UploadedDocument.id == payload.document_id,
        models.UploadedDocument.student_id == payload.student_id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    try:
        text, _ = pdf_processor.extract_text(doc.file_path)
        answer = pdf_processor.answer_pdf_question(text, payload.question)
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return schemas.PDFQuestionResponse(
        answer=answer,
        document_name=doc.original_name,
    )


@app.post("/notes/summarize/{document_id}", response_model=schemas.PDFSummaryResponse, tags=["Notes"])
def summarize_document(document_id: int, student_id: int, db: Session = Depends(get_db)):
    """Generate or retrieve a summary for an uploaded PDF."""
    doc = db.query(models.UploadedDocument).filter(
        models.UploadedDocument.id == document_id,
        models.UploadedDocument.student_id == student_id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    try:
        text, _ = pdf_processor.extract_text(doc.file_path)
        summary, key_points = pdf_processor.summarize_pdf(text)
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Cache the summary
    doc.summary = summary
    db.commit()

    return schemas.PDFSummaryResponse(
        summary=summary,
        key_points=key_points,
        document_name=doc.original_name,
    )


# ── Progress ───────────────────────────────────────────────────────────────────

@app.get("/progress/{student_id}", tags=["Progress"])
def get_progress(student_id: int, db: Session = Depends(get_db)):
    """Detailed progress report for a student."""
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    sessions = (
        db.query(models.StudySession)
        .filter(models.StudySession.student_id == student_id)
        .all()
    )
    completed = [s for s in sessions if s.is_completed]

    # Group completed by date for daily chart data
    daily_hours: dict = {}
    for s in completed:
        key = s.date.isoformat()
        daily_hours[key] = daily_hours.get(key, 0) + s.duration_hours

    quiz_history = (
        db.query(models.QuizResult)
        .filter(models.QuizResult.student_id == student_id)
        .order_by(models.QuizResult.taken_at)
        .all()
    )

    # Subject-wise hours (completed)
    subject_hours: dict = {}
    for s in completed:
        name = s.subject.name if s.subject else "Uncategorised"
        subject_hours[name] = subject_hours.get(name, 0) + s.duration_hours

    # Weekly progress
    from collections import defaultdict
    weekly: dict = defaultdict(float)
    for s in completed:
        # ISO week key: e.g. "2025-W23"
        year, week, _ = s.date.isocalendar()
        key = f"{year}-W{week:02d}"
        weekly[key] += s.duration_hours

    return {
        "student_id": student_id,
        "total_planned_hours": round(sum(s.duration_hours for s in sessions), 1),
        "completed_hours": round(sum(s.duration_hours for s in completed), 1),
        "total_sessions": len(sessions),
        "completed_sessions": len(completed),
        "daily_hours": dict(sorted(daily_hours.items())),
        "weekly_hours": dict(sorted(weekly.items())),
        "subject_hours": subject_hours,
        "quiz_scores": [
            {
                "topic": r.topic,
                "score": r.score_percentage,
                "taken_at": r.taken_at.isoformat(),
            }
            for r in quiz_history
        ],
    }
