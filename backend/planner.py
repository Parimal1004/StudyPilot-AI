"""
AI Study Planner for StudyPilot AI.
Generates a personalized, day-by-day study plan using the LLM.

Strategy: generate the plan in weekly chunks (7 days per LLM call) to stay
well within token limits of small/fast models like Groq llama-3.1-8b-instant.
Each chunk asks for sessions covering exactly those 7 days, then all chunks
are merged and persisted together.
"""
import logging
from datetime import date, timedelta
from typing import List

from sqlalchemy.orm import Session

from backend import models
from backend.schemas import StudyPlanSessionSchema
from utils.llm_client import chat_completion, parse_json_response

logger = logging.getLogger(__name__)

# Chunk size: number of days to plan per LLM call.
# 7 days keeps the JSON output small enough for 8B models (≤ ~2000 tokens).
_CHUNK_DAYS = 7

SYSTEM_PROMPT = """You are StudyPilot, an expert academic planner for college students.
Your job is to create a realistic, personalized study plan for a specific date range.

Rules:
- Cover ONLY the dates in the requested range (start_date to end_date, inclusive).
- NEVER exceed the student's daily study hours on any single day.
- Prioritize weak topics (mark them High priority).
- Balance subjects across the days.
- Include a mix of activities: Learn, Practice, Revision, Quiz, Mock Test.
- As exam_date approaches, increase Revision and Mock Test sessions.
- Each session object MUST have ALL of these fields:
    date        (string, YYYY-MM-DD)
    subject     (string)
    topic       (string)
    duration_hours (number, e.g. 1.5)
    activity    (exactly one of: Learn, Practice, Revision, Quiz, Mock Test)
    priority    (exactly one of: High, Medium, Low)
    objective   (string, one sentence)
- Return ONLY a raw JSON object — no markdown, no explanation:
  {"sessions": [ ... ]}
"""


def _subjects_block(student: models.Student) -> str:
    parts = []
    for subj in student.subjects:
        topics = ", ".join(subj.topics) if subj.topics else "General"
        weak = ", ".join(subj.weak_topics) if subj.weak_topics else "None"
        parts.append(
            f"  - {subj.name}: topics=[{topics}]  weak=[{weak}]"
        )
    return "\n".join(parts)


def _build_chunk_prompt(
    student: models.Student,
    chunk_start: date,
    chunk_end: date,
    subjects_block: str,
) -> str:
    days_to_exam = (student.exam_date - chunk_start).days
    return (
        f"Student: {student.name} | Level: {student.knowledge_level} | "
        f"Daily hours: {student.daily_study_hours}h | Exam: {student.exam_date} "
        f"({days_to_exam} days away)\n\n"
        f"Subjects:\n{subjects_block}\n\n"
        f"Generate study sessions for {chunk_start} to {chunk_end} only "
        f"({(chunk_end - chunk_start).days + 1} days). "
        f"Do not exceed {student.daily_study_hours}h per day. "
        f"Return the JSON object with a 'sessions' array."
    )


def _resolve_subject(subject_name: str, subject_map: dict) -> models.Subject | None:
    """Find the Subject ORM object by name, with fallback partial matching."""
    key = subject_name.lower().strip()
    if key in subject_map:
        return subject_map[key]
    for map_key, obj in subject_map.items():
        if map_key in key or key in map_key:
            return obj
    return None


def _parse_chunk(raw: str, chunk_label: str) -> List[dict]:
    """Parse one chunk's JSON response; log and return [] on failure."""
    try:
        data = parse_json_response(raw)
        sessions = data.get("sessions", [])
        if not isinstance(sessions, list):
            logger.warning("Chunk %s: 'sessions' is not a list", chunk_label)
            return []
        return sessions
    except RuntimeError as e:
        logger.warning("Chunk %s parse failed: %s", chunk_label, e)
        return []


def generate_study_plan(
    student: models.Student,
    db: Session,
) -> List[StudyPlanSessionSchema]:
    """
    Generate a study plan for the student in weekly chunks, persist to DB, return sessions.
    Deletes any existing incomplete sessions before regenerating.
    """
    # Remove previous incomplete sessions
    db.query(models.StudySession).filter(
        models.StudySession.student_id == student.id,
        models.StudySession.is_completed == False,  # noqa: E712
    ).delete()
    db.commit()

    subject_map = {s.name.lower(): s for s in student.subjects}
    subjects_block = _subjects_block(student)

    today = date.today()
    exam_date = student.exam_date
    total_days = (exam_date - today).days  # exclusive of exam day

    # Build list of (chunk_start, chunk_end) windows
    chunks: List[tuple[date, date]] = []
    cursor = today
    while cursor < exam_date:
        chunk_end = min(cursor + timedelta(days=_CHUNK_DAYS - 1), exam_date - timedelta(days=1))
        chunks.append((cursor, chunk_end))
        cursor = chunk_end + timedelta(days=1)

    logger.info(
        "Generating plan for student %d: %d days → %d chunks",
        student.id, total_days, len(chunks),
    )

    all_raw_sessions: List[dict] = []

    for i, (chunk_start, chunk_end) in enumerate(chunks):
        chunk_label = f"{chunk_start}→{chunk_end}"
        user_prompt = _build_chunk_prompt(student, chunk_start, chunk_end, subjects_block)

        try:
            raw = chat_completion(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.4,
                max_tokens=2048,   # 7 days × ~3 sessions × ~80 tokens each ≈ 1700 tokens max
                expect_json=True,
            )
        except RuntimeError as e:
            logger.warning("Chunk %s LLM call failed: %s — skipping", chunk_label, e)
            continue

        chunk_sessions = _parse_chunk(raw, chunk_label)
        logger.info("Chunk %s: %d sessions received", chunk_label, len(chunk_sessions))
        all_raw_sessions.extend(chunk_sessions)

    if not all_raw_sessions:
        raise RuntimeError(
            "The AI did not generate any study sessions. "
            "Please check your API key and try again."
        )

    # Validate and persist
    validated: List[StudyPlanSessionSchema] = []
    db_sessions: List[models.StudySession] = []

    for item in all_raw_sessions:
        try:
            session_schema = StudyPlanSessionSchema(**item)
        except Exception as e:
            logger.warning("Skipping invalid session from AI: %s | %s", item, e)
            continue

        subject_obj = _resolve_subject(session_schema.subject, subject_map)

        db_session = models.StudySession(
            student_id=student.id,
            subject_id=subject_obj.id if subject_obj else None,
            date=date.fromisoformat(session_schema.date),
            topic=session_schema.topic,
            duration_hours=session_schema.duration_hours,
            activity=session_schema.activity,
            priority=session_schema.priority,
            objective=session_schema.objective,
            is_completed=False,
        )
        db_sessions.append(db_session)
        validated.append(session_schema)

    db.add_all(db_sessions)
    db.commit()

    logger.info(
        "Saved %d study sessions for student %d (%d chunks processed)",
        len(validated), student.id, len(chunks),
    )
    return validated
