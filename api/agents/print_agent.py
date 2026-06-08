"""
Agent 05 – Print Sourcing
Receives a graphic specification and queries the internal vendor database to
produce competitive quotes, then selects the optimal supplier.
"""
import json
import math
import os
import random

USE_MOCK_AI = os.getenv("USE_MOCK_AI", "true").lower() == "true"

# ── Vendor database (always real – no AI required) ────────────────────────────

VENDORS = [
    {
        "vendor_id": "V001",
        "name": "PrintPros UK",
        "location": "Manchester, UK",
        "techniques": ["Screen Print", "DTG", "Embroidery"],
        "base_rate_usd": 1.80,
        "setup_fee_usd": 45,
        "min_order": 50,
        "turnaround_days": 7,
        "quality_rating": 4.7,
        "sustainability_certified": True,
        "notes": "ISO 9001 certified. Water-based inks standard.",
    },
    {
        "vendor_id": "V002",
        "name": "FastThreads US",
        "location": "Los Angeles, CA",
        "techniques": ["Screen Print", "Heat Transfer", "Sublimation"],
        "base_rate_usd": 1.50,
        "setup_fee_usd": 35,
        "min_order": 25,
        "turnaround_days": 5,
        "quality_rating": 4.3,
        "sustainability_certified": False,
        "notes": "Rush orders available (+20%). Accepts DHL shipments.",
    },
    {
        "vendor_id": "V003",
        "name": "EcoStitch Portugal",
        "location": "Porto, Portugal",
        "techniques": ["Embroidery", "Screen Print"],
        "base_rate_usd": 2.10,
        "setup_fee_usd": 50,
        "min_order": 100,
        "turnaround_days": 14,
        "quality_rating": 4.9,
        "sustainability_certified": True,
        "notes": "GOTS certified. Specialises in premium embroidery. Ships EU/UK duty-free.",
    },
    {
        "vendor_id": "V004",
        "name": "ColourWave India",
        "location": "Tiruppur, India",
        "techniques": ["Screen Print", "DTG", "Sublimation"],
        "base_rate_usd": 0.95,
        "setup_fee_usd": 20,
        "min_order": 200,
        "turnaround_days": 21,
        "quality_rating": 4.1,
        "sustainability_certified": False,
        "notes": "High-volume specialist. Best price at 500+ units. 30-day payment terms.",
    },
    {
        "vendor_id": "V005",
        "name": "AlphaInk Canada",
        "location": "Toronto, ON",
        "techniques": ["DTG", "Screen Print"],
        "base_rate_usd": 2.00,
        "setup_fee_usd": 40,
        "min_order": 30,
        "turnaround_days": 6,
        "quality_rating": 4.6,
        "sustainability_certified": True,
        "notes": "Carbon-neutral certified since 2022. Excellent for small premium runs.",
    },
]


def run(task_data: dict, graphic_spec: dict) -> dict:
    """
    Always uses real vendor logic — no AI flag needed.
    Returns list of quotes and the recommended vendor.
    """
    technique = graphic_spec.get("print_technique", "Screen Print")
    qty = task_data.get("quantity", 100)
    budget = task_data.get("budget_usd", 500)
    print_cost = graphic_spec.get("estimated_print_cost_per_unit_usd", 2.50)

    quotes = []
    for v in VENDORS:
        # Skip vendors that don't support the required technique
        if not any(t.lower() in technique.lower() for t in v["techniques"]):
            continue
        if qty < v["min_order"]:
            continue

        unit_cost = v["base_rate_usd"] + print_cost
        # Small-run premium
        if qty < 100:
            unit_cost *= 1.15
        total_cost = round(unit_cost * qty + v["setup_fee_usd"], 2)

        quotes.append(
            {
                "vendor_id": v["vendor_id"],
                "vendor_name": v["name"],
                "location": v["location"],
                "technique": technique,
                "unit_cost_usd": round(unit_cost, 2),
                "setup_fee_usd": v["setup_fee_usd"],
                "total_cost_usd": total_cost,
                "turnaround_days": v["turnaround_days"],
                "quality_rating": v["quality_rating"],
                "sustainability_certified": v["sustainability_certified"],
                "within_budget": total_cost <= budget,
                "notes": v["notes"],
            }
        )

    # Sort by score: weighted (quality × 0.4) + (budget fit × 0.4) + (speed × 0.2)
    max_cost = max((q["total_cost_usd"] for q in quotes), default=1)
    max_days = max((q["turnaround_days"] for q in quotes), default=1)
    for q in quotes:
        cost_score = 1 - (q["total_cost_usd"] / max_cost)
        speed_score = 1 - (q["turnaround_days"] / max_days)
        quality_score = (q["quality_rating"] - 4.0) / 1.0  # normalise 4.0–5.0 → 0–1
        q["score"] = round(
            quality_score * 0.4 + cost_score * 0.4 + speed_score * 0.2, 3
        )

    quotes.sort(key=lambda q: q["score"], reverse=True)

    recommended = quotes[0] if quotes else None

    return {
        "requested_technique": technique,
        "quantity": qty,
        "budget_usd": budget,
        "quotes": quotes,
        "recommended_vendor": recommended,
        "recommendation_rationale": _rationale(recommended, quotes) if recommended else "No vendors matched the requirements.",
    }


def _rationale(recommended: dict, all_quotes: list) -> str:
    savings = None
    if len(all_quotes) > 1:
        second_cost = all_quotes[1]["total_cost_usd"]
        savings = round(second_cost - recommended["total_cost_usd"], 2)

    parts = [
        f"{recommended['vendor_name']} scores highest on the quality/cost/speed matrix.",
        f"Rated {recommended['quality_rating']}/5.0 with {recommended['turnaround_days']}-day turnaround.",
    ]
    if recommended["sustainability_certified"]:
        parts.append("Sustainability certified — aligns with Luxe Collective ESG commitments.")
    if savings and savings > 0:
        parts.append(f"Saves ${savings} vs next-best option.")
    if not recommended["within_budget"]:
        parts.append(
            f"⚠️ Total cost ${recommended['total_cost_usd']} exceeds budget ${recommended.get('budget_usd', '?')}. "
            "Consider increasing budget or reducing quantity."
        )
    return " ".join(parts)
