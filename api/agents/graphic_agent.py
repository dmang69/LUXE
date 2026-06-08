"""
Agent 03 – Graphic Designer
Takes an approved logo concept and produces the full garment graphic
specification: placement, sizing, colour separations, and print-ready notes.
"""
import json
import os
import random

USE_MOCK_AI = os.getenv("USE_MOCK_AI", "true").lower() == "true"

_MOCK_GRAPHICS = [
    {
        "graphic_name": "Front Centre Statement",
        "placement": "Centre chest, 3 cm below neckline",
        "dimensions_cm": {"width": 12, "height": 10},
        "print_technique": "Screen Print (plastisol inks)",
        "colour_separations": 3,
        "layers": [
            {"layer": 1, "description": "Base knockout flood (white underbase for dark garments)"},
            {"layer": 2, "description": "Primary brand mark in main brand colour"},
            {"layer": 3, "description": "Accent detail / metallic highlight overlay"},
        ],
        "file_requirements": "Vector AI/EPS at 300 DPI; spot colours defined as Pantone",
        "garment_notes": "Works on 100% cotton jersey (S–3XL). Avoid polyester blends — inks may bleed.",
        "sustainability_flag": "Water-based ink alternative available — add 8% to print cost.",
        "estimated_print_cost_per_unit_usd": 2.40,
    },
    {
        "graphic_name": "Oversized Back Drop",
        "placement": "Upper back, centred, 2 cm below collar",
        "dimensions_cm": {"width": 30, "height": 25},
        "print_technique": "Direct-to-Garment (DTG)",
        "colour_separations": "Full colour (no limit)",
        "layers": [
            {"layer": 1, "description": "White pre-treatment layer for colour vibrancy"},
            {"layer": 2, "description": "Full photographic/illustrative graphic"},
        ],
        "file_requirements": "300 DPI PNG/TIFF with transparent background; sRGB colour space",
        "garment_notes": "Optimal on 100% ringspun cotton. Test wash colorfastness before bulk order.",
        "sustainability_flag": "DTG uses less water than screen print for short runs.",
        "estimated_print_cost_per_unit_usd": 5.80,
    },
    {
        "graphic_name": "Tonal Embroidery Badge",
        "placement": "Left chest (heart position), 8 × 8 cm",
        "dimensions_cm": {"width": 8, "height": 8},
        "print_technique": "Machine Embroidery",
        "colour_separations": 2,
        "layers": [
            {"layer": 1, "description": "Underlay stitches for stability"},
            {"layer": 2, "description": "Top-stitch logo in brand thread colours"},
        ],
        "file_requirements": "Vector artwork → digitised to DST/EMB by embroidery house",
        "garment_notes": "Suitable for polos, fleece, caps. Minimum stitch count: 3 000.",
        "sustainability_flag": "No inks or chemicals — inherently low-impact process.",
        "estimated_print_cost_per_unit_usd": 3.20,
    },
]


def run(task_data: dict, logo_concept: dict) -> dict:
    if USE_MOCK_AI:
        return _mock_graphic(task_data, logo_concept)
    return _ai_graphic(task_data, logo_concept)


def _mock_graphic(task_data: dict, logo_concept: dict) -> dict:
    spec = random.choice(_MOCK_GRAPHICS).copy()
    spec["brand_name"] = task_data.get("brand_name", "Brand")
    spec["product_type"] = task_data.get("product_type", "Garment")
    spec["logo_concept_reference"] = logo_concept.get("concept_name", "Logo Concept")
    return spec


def _ai_graphic(task_data: dict, logo_concept: dict) -> dict:
    try:
        import google.generativeai as genai

        genai.configure(api_key=os.environ["GENAI_API_KEY"])
        model = genai.GenerativeModel("gemini-pro")

        prompt = f"""You are Agent 03 – Graphic Designer for Luxe Collective.
Create a full garment graphic specification based on the approved logo concept.

Brand: {task_data.get('brand_name')}
Product Type: {task_data.get('product_type')}
Style: {task_data.get('style_description')}
Logo Concept: {json.dumps(logo_concept, indent=2)}

Respond with a JSON object with these exact keys:
- graphic_name (string)
- placement (string: exact garment position)
- dimensions_cm (object: width and height as numbers)
- print_technique (string: Screen Print | DTG | Embroidery | Heat Transfer | Sublimation)
- colour_separations (number or string)
- layers (array of objects with layer number and description)
- file_requirements (string)
- garment_notes (string)
- sustainability_flag (string)
- estimated_print_cost_per_unit_usd (number)

Be precise and production-ready in your specifications."""

        response = model.generate_content(prompt)
        text = response.text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        result = json.loads(text)
        result["brand_name"] = task_data.get("brand_name", "Brand")
        result["product_type"] = task_data.get("product_type", "Garment")
        result["logo_concept_reference"] = logo_concept.get("concept_name", "Logo Concept")
        return result
    except Exception as exc:
        fallback = _mock_graphic(task_data, logo_concept)
        fallback["error"] = str(exc)
        fallback["note"] = "Fell back to mock graphic spec due to AI error."
        return fallback
