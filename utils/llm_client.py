"""
LLM client helper for StudyPilot AI.
Supports OpenAI-compatible APIs (OpenAI, Groq, Together, etc.)

Notes on Groq compatibility:
- response_format={"type":"json_object"} is NOT supported by all Groq models
  (llama-3.1-8b-instant returns 400 json_validate_failed).
  We enforce JSON via prompt instructions instead and strip it for non-OpenAI hosts.
"""
import os
import json
import logging
from openai import OpenAI, APIError, RateLimitError, APITimeoutError
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Hosts that reliably support response_format=json_object
_JSON_MODE_HOSTS = {"api.openai.com", "api.together.xyz"}


def _get_client() -> OpenAI:
    api_key = os.getenv("LLM_API_KEY", "")
    base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    if not api_key:
        raise RuntimeError(
            "LLM_API_KEY is not set. Please configure it in your .env file."
        )
    return OpenAI(api_key=api_key, base_url=base_url)


def _get_model() -> str:
    return os.getenv("LLM_MODEL", "gpt-4o-mini")


def _supports_json_mode() -> bool:
    """Return True only for hosts known to support response_format=json_object."""
    base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    return any(host in base_url for host in _JSON_MODE_HOSTS)


def chat_completion(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    expect_json: bool = False,
) -> str:
    """
    Call the LLM and return the assistant's message text.
    When expect_json=True and the host does not support json_object mode,
    the JSON instruction is enforced via prompt instead.
    Raises a user-friendly RuntimeError on failure.
    """
    client = _get_client()
    model = _get_model()

    # For hosts that don't support response_format, append a reminder to the
    # system prompt so the model still returns clean JSON.
    sys_prompt = system_prompt
    if expect_json and not _supports_json_mode():
        sys_prompt = (
            system_prompt.rstrip()
            + "\n\nIMPORTANT: Your entire response must be valid JSON only. "
            "No prose, no markdown fences, no explanation — raw JSON only."
        )

    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_prompt},
    ]

    kwargs: dict = dict(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    # Only attach response_format where it is supported
    if expect_json and _supports_json_mode():
        kwargs["response_format"] = {"type": "json_object"}

    try:
        response = client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content or ""
        if not content.strip():
            finish = getattr(response.choices[0], "finish_reason", "unknown")
            logger.error("LLM returned empty content. finish_reason=%s", finish)
            raise RuntimeError(
                "The AI returned an empty response. "
                "This usually means the output was too long — try reducing your exam timeframe "
                "or the number of subjects, then try again."
            )
        return content
    except RateLimitError:
        raise RuntimeError(
            "The AI service is currently rate-limited. Please wait a moment and try again."
        )
    except APITimeoutError:
        raise RuntimeError(
            "The AI service timed out. Please try again."
        )
    except APIError as e:
        # Surface the actual Groq/OpenAI error message to the log for diagnosis
        logger.error("LLM API error: %s", e)
        msg = str(e)
        if "json_validate_failed" in msg:
            raise RuntimeError(
                "The AI could not produce a valid JSON response. "
                "Please try again — if the problem persists, reduce the exam timeframe."
            )
        raise RuntimeError(
            "The AI service returned an error. Please check your API key and try again."
        )
    except RuntimeError:
        raise  # already user-friendly
    except Exception as e:
        logger.error("Unexpected LLM error: %s", e)
        raise RuntimeError("An unexpected error occurred while calling the AI service.")


def parse_json_response(raw: str) -> dict:
    """
    Safely parse a JSON response from the LLM.
    Strips markdown code fences if present.
    """
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        # remove first and last fence lines
        text = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse LLM JSON: %s\nRaw: %s", e, raw[:500])
        raise RuntimeError(
            "The AI returned an unexpected response format. Please try again."
        )
