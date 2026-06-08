from typing import Dict, List

from agents.abstract_agent import SpecializedAgentClient

_PLACEMENTS: Dict[str, str] = {
    "hoodie": "center chest + full back",
    "tee": "left chest + full back",
    "joggers": "left thigh + back right calf",
    "jacket": "left chest + full back",
    "dress": "left hip + full back",
    "top": "center chest",
    "bottom": "left thigh",
}

_SCALES: Dict[str, str] = {
    "hoodie": 'large (10"x10")',
    "tee": 'medium (8"x8")',
    "joggers": 'medium (6"x6")',
    "jacket": 'large (10"x8")',
    "dress": 'medium (8"x6")',
    "top": 'small (4"x4")',
    "bottom": 'small (4"x4")',
}


class GraphicDesignSpecialist(SpecializedAgentClient):
    """Agent 03 – Graphic designer for garment collection artwork."""

    def __init__(self, boss_api_url: str = "http://localhost:8000/api/boss"):
        super().__init__("03", boss_api_url)

    async def create_work(self, **kwargs) -> Dict:
        return await self.create_collection_graphics(**kwargs)

    async def create_collection_graphics(
        self,
        collection_name: str,
        garment_types: List[str],
    ) -> Dict:
        """Create garment graphics and submit to Boss Agent for approval."""
        payload = {
            "collection": collection_name,
            "garments": garment_types,
            "designs": [
                {
                    "garment": gt,
                    "concept": f"Ancient symbol pattern for {gt}",
                    "placement": _PLACEMENTS.get(gt, "center chest"),
                    "scale": _SCALES.get(gt, 'medium (8"x8")'),
                    "colorways": [
                        {"name": "Monochrome", "colors": ["#000000", "#FFFFFF"]},
                        {"name": "Earth Tones", "colors": ["#8B4513", "#DEB887", "#FFFFFF"]},
                        {"name": "Jewel Tones", "colors": ["#8B0000", "#000080", "#FFD700", "#FFFFFF"]},
                    ],
                    "file_format": "print-ready PNG/SVG",
                    "repeat_pattern": True,
                }
                for gt in garment_types
            ],
            "production_notes": [
                "All designs use water-based, eco-friendly inks",
                "Minimum 300 DPI for print quality",
                'Include 0.125" bleed for all-over prints',
            ],
        }
        description = f"Graphic designs for {collection_name} collection"
        return await self.submit_for_approval(
            task_type="design_concept",
            description=description,
            payload=payload,
        )
