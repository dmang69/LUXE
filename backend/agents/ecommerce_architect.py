"""
Agent 06 – E-Commerce Architect
(Storefront, product catalog, checkout flow)
"""
from typing import Optional
from .abstract_agent import SpecializedAgentClient


class EcommerceArchitect(SpecializedAgentClient):
    def __init__(self, boss_api_url: str = None):
        super().__init__("06", boss_api_url)

    async def update_product_listing(
        self,
        product_ids: list,
        updates: dict,
        reason: Optional[str] = None,
    ) -> dict:
        """
        Bulk-update product catalogue entries.
        `updates` may include: price, description, image_url, seo_tags, is_active.
        """
        payload = {
            "product_ids": product_ids,
            "updates": updates,
            "reason": reason or "AI-driven optimisation based on latest trend/sales data",
        }
        await self.log_activity(
            "catalog_update_requested",
            f"Bulk update of {len(product_ids)} product(s): {list(updates.keys())}",
        )
        return await self.submit_for_approval(
            task_type="catalog_update",
            description=f"Bulk update of {len(product_ids)} product(s)",
            payload=payload,
        )

    async def create_product(
        self,
        sku: str,
        name: str,
        description: str,
        price: float,
        category: str,
        image_prompt: Optional[str] = None,
    ) -> dict:
        """Create a new product listing (pending Boss approval)."""
        payload = {
            "sku": sku,
            "name": name,
            "description": description,
            "price": price,
            "category": category,
            "image_prompt": image_prompt,
        }
        await self.log_activity("new_product_draft", f"Draft product: {name} ({sku})")
        return await self.submit_for_approval(
            task_type="create_product",
            description=f"Create product: {name} ({sku}) @ ${price}",
            payload=payload,
        )
