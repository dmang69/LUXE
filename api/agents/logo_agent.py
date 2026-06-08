"""
Agent 02 – Logo Designer
Generates a detailed logo concept for an approved creative brief.
"""
import json
import os
import random

USE_MOCK_AI = os.getenv("USE_MOCK_AI", "true").lower() == "true"

_MOCK_CONCEPTS = [
    {
        "concept_name": "Minimalist Serif Mark",
        "primary_symbol": "A bold, single uppercase initial in a custom geometric serif typeface",
        "color_palette": ["#1A1A2E", "#E8D5B7", "#C9A96E"],
        "color_names": ["Midnight Navy", "Warm Ivory", "Antique Gold"],
        "typography": "Custom serif with slight Art Deco influence — sharp terminals, high contrast strokes",
        "style_notes": "Logo sits inside a thin rectangular frame. Negative space conveys luxury and restraint.",
        "usage": "Embroidered on garment chest; foil-stamped on swing tags; embossed on packaging",
        "rationale": "Clean geometry signals premium positioning while the gold accent drives aspirational appeal.",
    },
    {
        "concept_name": "Heritage Crest",
        "primary_symbol": "Shield crest with stylised laurel branches and brand initial monogram",
        "color_palette": ["#2C1810", "#D4AF37", "#F5F5DC"],
        "color_names": ["Rich Espresso", "Classic Gold", "Cream"],
        "typography": "Refined small-caps with generous letter-spacing for brand name beneath crest",
        "style_notes": "Detailed line-art crest that reduces cleanly to single-colour for embroidery.",
        "usage": "Woven label, heat-transfer on inner neck, debossed leather patch",
        "rationale": "Heritage aesthetic resonates with buyers seeking provenance and authenticity.",
    },
    {
        "concept_name": "Abstract Thread Mark",
        "primary_symbol": "Three interlocking curved lines evoking both a thread spool and the letter 'L'",
        "color_palette": ["#0D0D0D", "#FFFFFF", "#FF6B35"],
        "color_names": ["Jet Black", "Pure White", "Ember Orange"],
        "typography": "Lowercase geometric sans-serif — approachable yet precise",
        "style_notes": "Mark works as standalone icon or paired with wordmark. Orange acts as energy accent.",
        "usage": "Screen-printed on streetwear drops; tone-on-tone emboss for premium lines",
        "rationale": "Modern iconography differentiates from legacy fashion brands targeting a younger audience.",
    },
]


def run(task_data: dict, boss_feedback: str = "") -> dict:
    if USE_MOCK_AI:
        return _mock_concept(task_data)
    return _ai_concept(task_data, boss_feedback)


def _mock_concept(task_data: dict) -> dict:
    concept = random.choice(_MOCK_CONCEPTS).copy()
    concept["brand_name"] = task_data.get("brand_name", "Brand")
    concept["product_type"] = task_data.get("product_type", "Garment")
    return concept


def _ai_concept(task_data: dict, boss_feedback: str) -> dict:
    try:
        import google.generativeai as genai

        genai.configure(api_key=os.environ["GENAI_API_KEY"])
        model = genai.GenerativeModel("gemini-pro")

        prompt = f"""You are Agent 02 – Logo Designer for Luxe Collective, a premium fashion brand.
Create a detailed logo concept for this approved brief.

Brand Name: {task_data.get('brand_name')}
Product Type: {task_data.get('product_type')}
Style Description: {task_data.get('style_description')}
Boss Agent Feedback: {boss_feedback}

Respond with a JSON object with these exact keys:
- concept_name (string)
- primary_symbol (string: describe the visual mark)
- color_palette (array of 3 hex codes)
- color_names (array of 3 descriptive colour names)
- typography (string: font style description)
- style_notes (string: design execution details)
- usage (string: where/how the logo will appear on garments)
- rationale (string: why this concept fits the brand)

Be specific and fashion-industry professional."""

        response = model.generate_content(prompt)
        text = response.text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        result = json.loads(text)
        result["brand_name"] = task_data.get("brand_name", "Brand")
        result["product_type"] = task_data.get("product_type", "Garment")
        return result
    except Exception as exc:
        fallback = _mock_concept(task_data)
        fallback["error"] = str(exc)
        fallback["note"] = "Fell back to mock concept due to AI error."
        return fallback
