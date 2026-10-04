"""
AI Quiz generator and scorer for StudyPilot AI.
"""
import logging
import uuid
from typing import List

from sqlalchemy.orm import Session

from backend import models
from backend.schemas import (
    QuizQuestion,
    QuizOption,
    QuizSubmission,
    QuizResultOut,
)
from utils.llm_client import chat_completion, parse_json_response

logger = logging.getLogger(__name__)

QUIZ_SYSTEM_PROMPT = """You are an expert academic quiz creator.
Generate high-quality multiple-choice questions (MCQs) for college students.

Rules:
- Each question must have exactly 4 options labeled A, B, C, D.
- Provide the correct answer label (A/B/C/D).
- Provide a clear explanation for the correct answer.
- Questions must be relevant to the given topic and difficulty.
- Return ONLY valid JSON: {"questions": [ {
    "question_number": 1,
    "question": "...",
    "options": [{"label": "A", "text": "..."}, ...],
    "correct_answer": "A",
    "explanation": "..."
  }, ... ]}
"""


def generate_quiz(
    subject: str,
    topic: str,
    difficulty: str,
    num_questions: int,
    knowledge_level: str = "Intermediate",
) -> List[QuizQuestion]:
    """Generate MCQ questions using the LLM."""
    user_prompt = (
        f"Subject: {subject}\n"
        f"Topic: {topic}\n"
        f"Difficulty: {difficulty}\n"
        f"Student Knowledge Level: {knowledge_level}\n"
        f"Number of Questions: {num_questions}\n\n"
        "Generate the quiz questions as specified."
    )

    raw = chat_completion(
        system_prompt=QUIZ_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.6,
        max_tokens=4000,
        expect_json=True,
    )
    data = parse_json_response(raw)
    raw_questions = data.get("questions", [])

    questions: List[QuizQuestion] = []
    for q in raw_questions:
        try:
            questions.append(QuizQuestion(**q))
        except Exception as e:
            logger.warning("Skipping invalid question: %s | %s", q, e)

    if not questions:
        raise RuntimeError("The AI did not generate any quiz questions. Please try again.")

    return questions


def score_quiz(
    submission: QuizSubmission,
    student_id: int,
    db: Session,
) -> QuizResultOut:
    """Score the submitted quiz, store results, identify weak areas."""
    questions = submission.questions
    answers = submission.answers

    correct = 0
    detailed = []
    weak_areas: List[str] = []

    for q in questions:
        qnum = str(q.question_number)
        chosen = answers.get(qnum, "")
        is_correct = chosen.upper() == q.correct_answer.upper()
        if is_correct:
            correct += 1
        else:
            # Mark topic as weak area
            weak_areas.append(q.question[:60])

        detailed.append(
            {
                "question_number": q.question_number,
                "question": q.question,
                "chosen": chosen,
                "correct_answer": q.correct_answer,
                "is_correct": is_correct,
                "explanation": q.explanation,
            }
        )

    total = len(questions)
    score_pct = round((correct / total) * 100, 1) if total > 0 else 0.0

    if score_pct >= 80:
        feedback = "Excellent work! You have a strong grasp of this topic."
    elif score_pct >= 60:
        feedback = "Good effort! Review the incorrect answers to strengthen your understanding."
    elif score_pct >= 40:
        feedback = "You're making progress. Focus on the weak areas and revise the topic."
    else:
        feedback = "Keep practicing! Review the material carefully and attempt the quiz again."

    # Resolve subject FK
    subject_obj = (
        db.query(models.Subject)
        .filter(
            models.Subject.student_id == student_id,
            models.Subject.name.ilike(f"%{submission.subject}%"),
        )
        .first()
    )

    # Persist result
    quiz_result = models.QuizResult(
        student_id=student_id,
        subject_id=subject_obj.id if subject_obj else None,
        topic=submission.topic,
        difficulty=submission.difficulty,
        total_questions=total,
        correct_answers=correct,
        score_percentage=score_pct,
        weak_areas=weak_areas[:5],  # store top 5 weak question snippets
    )
    db.add(quiz_result)

    # Update subject weak topics if score is poor
    if score_pct < 60 and subject_obj:
        existing_weak = set(subject_obj.weak_topics or [])
        existing_weak.add(submission.topic)
        subject_obj.weak_topics = list(existing_weak)

    db.commit()

    return QuizResultOut(
        total_questions=total,
        correct_answers=correct,
        score_percentage=score_pct,
        weak_areas=weak_areas[:5],
        feedback=feedback,
        detailed=detailed,
    )
