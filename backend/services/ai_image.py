"""
AI image-generation service wrapper.
Tries Google Imagen (via generativeai), then OpenAI DALL-E, then returns None.
Set GOOGLE_API_KEY or OPENAI_API_KEY in the environment to enable real generation.
"""
import os
import base64
import logging
from typing import Optional

logger = logging.getLogger(__name__)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


async def generate_image(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    style: str = "vivid",
) -> Optional[bytes]:
    """
    Generate an image from a text prompt.
    Returns raw PNG/JPEG bytes, or None if no provider is configured.
    """
    if OPENAI_API_KEY:
        return await _openai_generate(prompt, width, height, style)

    if GOOGLE_API_KEY:
        return await _google_generate(prompt)

    logger.warning("No AI image provider configured – set OPENAI_API_KEY or GOOGLE_API_KEY")
    return None


async def _openai_generate(prompt: str, width: int, height: int, style: str) -> Optional[bytes]:
    try:
        from openai import AsyncOpenAI
        import httpx

        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        size_str = f"{width}x{height}" if f"{width}x{height}" in (
            "256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"
        ) else "1024x1024"

        response = await client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size=size_str,
            style=style,
            response_format="b64_json",
        )
        b64 = response.data[0].b64_json
        return base64.b64decode(b64)
    except Exception as exc:
        logger.error("OpenAI image generation failed: %s", exc)
        return None


async def _google_generate(prompt: str) -> Optional[bytes]:
    try:
        import google.generativeai as genai

        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.ImageGenerationModel("imagen-3.0-generate-001")
        result = model.generate_images(prompt=prompt, number_of_images=1)
        img = result.images[0]
        return img._image_bytes
    except Exception as exc:
        logger.error("Google image generation failed: %s", exc)
        return None
