"""
Agent 01 – Boss Agent
Reviews a creative brief and either approves it (with constructive feedback)
or rejects it (with clear reasons and suggestions to improve).
"""
import json
import os
import random

USE_MOCK_AI = os.getenv("USE_MOCK_AI", "true").lower() == "true"

_APPROVALS = [
    "Approved ✅ — Clear brand identity and well-defined target aesthetic. "
    "Brief is actionable. Proceeding to logo concept phase.",
    "Approved ✅ — Strong concept with differentiated style direction. "
    "Brand name is memorable. Moving to design pipeline.",
    "Approved ✅ — Good product specification and realistic budget. "
    "Style description is detailed enough for design execution.",
]

_REJECTIONS = [
    "Rejected ❌ — Style description is too vague. Please add at least 3 specific "
    "visual references (colours, motifs, inspirations) and resubmit.",
    "Rejected ❌ — Budget is below minimum for requested quantity. "
    "Increase budget or reduce quantity and resubmit.",
    "Rejected ❌ — Brand name conflicts with existing trademarks in our database. "
    "Please choose a unique name and resubmit.",
]


def run(task_data: dict) -> dict:
    """
    Returns a dict with keys: status ('approved'|'rejected'), feedback (str).
    """
    if USE_MOCK_AI:
        return _mock_review(task_data)
    return _ai_review(task_data)


def _mock_review(task_data: dict) -> dict:
    # For demo: approve if style_description >= 20 chars, reject otherwise
    desc = task_data.get("style_description", "")
    budget = task_data.get("budget_usd", 500)
    qty = task_data.get("quantity", 100)

    if len(desc) < 20:
        return {
            "status": "rejected",
            "feedback": (
                "Rejected ❌ — Style description is too brief. "
                "Please provide at least 20 characters describing the visual direction."
            ),
        }
    if budget < qty * 2:
        return {
            "status": "rejected",
            "feedback": (
                f"Rejected ❌ — Budget ${budget} is insufficient for {qty} units. "
                "Minimum recommended: $2 per unit. Please revise."
            ),
        }
    return {"status": "approved", "feedback": random.choice(_APPROVALS)}


def _ai_review(task_data: dict) -> dict:
    try:
        import google.generativeai as genai

        genai.configure(api_key=os.environ["GENAI_API_KEY"])
        model = genai.GenerativeModel("gemini-pro")

        prompt = f"""You are the Boss Agent for Luxe Collective, a premium fashion brand.
Review this creative brief and decide whether to APPROVE or REJECT it.

Brand Name: {task_data.get('brand_name')}
Product Type: {task_data.get('product_type')}
Style Description: {task_data.get('style_description')}
Quantity: {task_data.get('quantity')}
Budget (USD): {task_data.get('budget_usd')}

Respond with a JSON object like:
{{"status": "approved", "feedback": "your feedback here"}}
or
{{"status": "rejected", "feedback": "your rejection reason and improvement suggestions"}}

Be concise (1-2 sentences). Start feedback with "Approved ✅ —" or "Rejected ❌ —"."""

        response = model.generate_content(prompt)
        # Strip markdown code fences if present
        text = response.text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        return json.loads(text)
    except Exception as exc:
        return {
            "status": "rejected",
            "feedback": f"Boss Agent encountered an error: {exc}. Please check your GENAI_API_KEY.",
        }
