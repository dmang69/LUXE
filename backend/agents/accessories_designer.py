"""
Agent 04 – Accessories Designer
(Handbags, wallets, footwear, underwear)
"""
from .abstract_agent import SpecializedAgentClient


class AccessoriesDesigner(SpecializedAgentClient):
    def __init__(self, boss_api_url: str = None):
        super().__init__("04", boss_api_url)

    async def design_accessory_line(
        self,
        category: str,
        collection_name: str,
        sku_count: int = 5,
    ) -> dict:
        """
        Generate accessory SKU concepts and submit for Boss approval.
        In production the image_prompt feeds an image-generation model (see services/ai_image.py).
        """
        payload = {
            "collection": collection_name,
            "category": category,
            "skus": [
                {
                    "sku": f"{category.upper()}-{i:03d}",
                    "name": f"{collection_name} {category.title()} {i}",
                    "description": f"AI-generated {category} concept for {collection_name}",
                    "materials": self._materials(category),
                    "dimensions_cm": self._dims(category),
                    "price_target_usd": round(120 + i * 15, 2),
                    "image_prompt": (
                        f"{category} {collection_name} luxury, "
                        f"{self._style()}, high detail"
                    ),
                }
                for i in range(1, sku_count + 1)
            ],
            "notes": [
                f"All {category}s use sustainable/vegan materials where applicable",
                "Production-ready tech packs generated after approval",
            ],
        }

        await self.log_activity(
            "design_start",
            f"Designing {sku_count}-piece {category} line for '{collection_name}'",
        )
        return await self.submit_for_approval(
            task_type="design_concept",
            description=f"{sku_count}-piece {category} line for {collection_name}",
            payload=payload,
        )

    # ── helpers ────────────────────────────────────────────────────────────

    def _materials(self, cat: str) -> list:
        opts = {
            "handbag":   ["Full-grain leather", "Vegan polyurethane", "Canvas"],
            "wallet":    ["Top-grain leather", "Recycled nylon", "Cork"],
            "footwear":  ["Leather upper", "Synthetic mesh", "Natural rubber sole"],
            "underwear": ["Organic cotton", "Bamboo viscose", "Modal"],
        }
        return opts.get(cat, ["Premium material"])

    def _dims(self, cat: str) -> dict:
        base = {
            "handbag":   (30, 15, 10),
            "wallet":    (11, 8, 2),
            "footwear":  (28, 10, 5),
            "underwear": (0, 0, 0),
        }
        l, w, h = base.get(cat, (10, 10, 10))
        return {"length": l, "width": w, "height": h}

    def _style(self) -> str:
        styles = [
            "Art Deco", "Minimalist", "Tribal",
            "Futuristic", "Vintage", "Avant-garde",
        ]
        return styles[hash(self.agent_id) % len(styles)]
