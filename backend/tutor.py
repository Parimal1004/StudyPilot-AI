"""
AI Tutor for StudyPilot AI.
Answers student doubts adapted to their knowledge level.
"""
import logging
from utils.llm_client import chat_completion

logger = logging.getLogger(__name__)

TUTOR_SYSTEM_PROMPT = """You are StudyPilot Tutor, a friendly and knowledgeable academic tutor for college students.
Your explanations are clear, accurate, and adapted to the student's knowledge level.

Adapt your language:
- Beginner: Use simple words, everyday analogies, and avoid jargon.
- Intermediate: Use standard academic language with some technical terms explained.
- Advanced: Use precise technical vocabulary and deeper analysis.

Explanation types:
- Simple Explanation: 2-3 clear sentences, plain language.
- Detailed Explanation: Thorough explanation covering the concept from multiple angles.
- Example: Provide 1-2 concrete, relatable examples to illustrate the concept.
- Step-by-Step: Break the concept or process into numbered steps.

Always be encouraging and end with a brief tip or reminder if helpful.
"""


def answer_question(
    question: str,
    explanation_type: str,
    knowledge_level: str,
    subject_context: str | None = None,
) -> str:
    """
    Generate a tutor response for the student's question.
    """
    context_line = f"Subject Context: {subject_context}\n" if subject_context else ""
    user_prompt = (
        f"{context_line}"
        f"Student Knowledge Level: {knowledge_level}\n"
        f"Explanation Type Requested: {explanation_type}\n\n"
        f"Student's Question:\n{question}"
    )

    return chat_completion(
        system_prompt=TUTOR_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.7,
        max_tokens=1500,
        expect_json=False,
    )
