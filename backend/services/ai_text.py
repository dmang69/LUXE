"""
AI text-generation service wrapper.
Tries Google Gemini, then OpenAI GPT-4, then returns a mock response.
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
OPENAI_MODEL   = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


async def generate_text(
    prompt: str,
    system_prompt: str = "You are a luxury fashion brand copywriter.",
    max_tokens: int = 500,
) -> str:
    """
    Generate text from a prompt.
    Falls back to a mock response if no provider is configured.
    """
    if GOOGLE_API_KEY:
        result = await _gemini_generate(prompt, system_prompt, max_tokens)
        if result:
            return result

    if OPENAI_API_KEY:
        result = await _openai_generate(prompt, system_prompt, max_tokens)
        if result:
            return result

    logger.warning("No AI text provider configured – returning mock response")
    return _mock_response(prompt)


async def _gemini_generate(prompt: str, system_prompt: str, max_tokens: int) -> Optional[str]:
    try:
        import google.generativeai as genai

        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel(
            GEMINI_MODEL,
            system_instruction=system_prompt,
        )
        response = await model.generate_content_async(
            prompt,
            generation_config={"max_output_tokens": max_tokens},
        )
        return response.text
    except Exception as exc:
        logger.error("Gemini text generation failed: %s", exc)
        return None


async def _openai_generate(prompt: str, system_prompt: str, max_tokens: int) -> Optional[str]:
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": prompt},
            ],
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
    except Exception as exc:
        logger.error("OpenAI text generation failed: %s", exc)
        return None


def _mock_response(prompt: str) -> str:
    """Placeholder when no AI provider is available."""
    return (
        "Crafted for the connoisseur who demands nothing less than perfection. "
        "Each piece whispers the ancient secrets of master artisans, fused with "
        "the boldness of tomorrow's visionaries. Wear the extraordinary."
    )
