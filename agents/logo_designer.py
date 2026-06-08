from typing import Dict, List

from agents.abstract_agent import SpecializedAgentClient


# Symbol and palette reference data
_SYMBOLS: Dict[str, List[str]] = {
    "Egyptian": ["ankh", "eye of horus", "lotus", "scarab", "hieroglyphic cartouche"],
    "Norse": ["valknut", "helm of awe", "thor's hammer", "yorvik serpent", "runic compass"],
    "Celtic": ["trinity knot", "claddagh", "spiral", "tree of life", "shield knot"],
    "Sumerian": ["cuneiform tablet", "winged disk", "tree of life", "lion griffin"],
    "Mayan": ["jade mask", "serpent bar", "calendar glyph", "maize god", "quetzal bird"],
}

_PALETTES: Dict[str, List[str]] = {
    "Egyptian": ["#000080", "#FFD700", "#8B0000", "#FFFFFF"],
    "Norse": ["#8B0000", "#000080", "#FFFFFF", "#FFD700"],
    "Celtic": ["#006400", "#8B4513", "#FFFFFF", "#FFD700"],
    "Sumerian": ["#8B4513", "#DAA520", "#FFFFFF", "#000080"],
    "Mayan": ["#006400", "#FF8C00", "#8B0000", "#FFFFFF"],
}


class AncientSymbolLogoDesigner(SpecializedAgentClient):
    """Agent 02 – Logo designer specialising in ancient cultural symbolism."""

    def __init__(self, boss_api_url: str = "http://localhost:8000/api/boss"):
        super().__init__("02", boss_api_url)

    async def create_work(self, **kwargs) -> Dict:
        return await self.generate_logo_variations(**kwargs)

    async def generate_logo_variations(
        self,
        culture: str,
        product_line: str,
        num_variations: int = 3,
    ) -> Dict:
        """Generate logo concepts and submit to Boss Agent for approval."""
        base_url = "https://storage.luxe-collective.com/logos"
        payload = {
            "culture": culture,
            "product_line": product_line,
            "variations": [
                {
                    "id": f"var_{i + 1}",
                    "description": f"Logo variation {i + 1} inspired by {culture} symbolism",
                    "elements": _SYMBOLS.get(culture, ["geometric pattern", "sacred geometry"]),
                    "mockup_url": f"{base_url}/{culture}_var_{i + 1}.png",
                    "svg_url": f"{base_url}/{culture}_var_{i + 1}.svg",
                }
                for i in range(num_variations)
            ],
            "style_guide": {
                "primary_colors": _PALETTES.get(culture, ["#000000", "#FFFFFF", "#808080"]),
                "secondary_colors": ["#000000", "#FFFFFF"],
                "usage_guidelines": [
                    "For premium apparel only",
                    "Maintain 10% clear space",
                ],
            },
        }
        description = f"Logo concepts for {product_line} using {culture} ancient symbolism"
        return await self.submit_for_approval(
            task_type="design_concept",
            description=description,
            payload=payload,
        )
