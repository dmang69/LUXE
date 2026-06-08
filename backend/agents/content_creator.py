"""
Agent 08 – Content Creator
(Product descriptions, blog posts, social captions)
"""
import os
from typing import Optional
import httpx
from .abstract_agent import SpecializedAgentClient, API_BASE_URL


class ContentCreator(SpecializedAgentClient):
    def __init__(self, boss_api_url: str = None):
        super().__init__("08", boss_api_url)

    async def generate_product_copy(
        self,
        product_ids: list,
        copy_type: str = "description",
        tone: str = "luxury, mystical, ancient",
    ) -> dict:
        """
        Stage product-copy generation for Boss approval.
        After approval the executor calls the LLM (services/ai_text.py) and
        writes the result back to the product table.
        """
        product_data = await self._fetch_products(product_ids)

        payload = {
            "product_ids": product_ids,
            "copy_type": copy_type,
            "tone": tone,
            "generated_copy": {},        # filled by the executor after calling the LLM
            "product_context": product_data,
        }
        await self.log_activity(
            "content_draft",
            f"Queuing {copy_type} copy for {len(product_ids)} product(s)",
        )
        return await self.submit_for_approval(
            task_type="content_creation",
            description=f"Generate {copy_type} for {len(product_ids)} product(s)",
            payload=payload,
        )

    async def generate_blog_post(
        self,
        title: str,
        topic: str,
        keywords: Optional[list] = None,
        word_count: int = 800,
    ) -> dict:
        """Draft a blog post (pending Boss approval)."""
        payload = {
            "title": title,
            "topic": topic,
            "keywords": keywords or [],
            "word_count": word_count,
            "content": "",   # filled by executor
        }
        await self.log_activity("blog_draft", f"Blog draft: '{title}'")
        return await self.submit_for_approval(
            task_type="blog_post",
            description=f"Write blog post: {title}",
            payload=payload,
        )

    async def _fetch_products(self, ids: list) -> list:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{API_BASE_URL}/api/admin/sales/products",
                    params={"limit": 200},
                )
                if resp.status_code == 200:
                    all_products = resp.json()
                    return [p for p in all_products if p["id"] in ids]
        except Exception:
            pass
        return [{"id": pid, "name": f"Product {pid}"} for pid in ids]
