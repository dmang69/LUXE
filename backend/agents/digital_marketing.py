"""
Agent 07 – Digital Marketing & Promotion
"""
from datetime import datetime, timedelta
from typing import Optional
from .abstract_agent import SpecializedAgentClient


class DigitalMarketingAgent(SpecializedAgentClient):
    def __init__(self, boss_api_url: str = None):
        super().__init__("07", boss_api_url)

    async def create_campaign(
        self,
        name: str,
        channels: list,
        budget_usd: float,
        target_audience: dict,
        creative_asset_ids: Optional[list] = None,
        flight_days: int = 14,
    ) -> dict:
        """
        Build a multi-channel marketing campaign and submit for Boss approval.
        After approval the executor stores it in the Campaign table.
        """
        now = datetime.utcnow()
        payload = {
            "campaign_name": name,
            "channels": channels,
            "budget_usd": budget_usd,
            "target_audience": target_audience,
            "creative_asset_ids": creative_asset_ids or [],
            "flight_dates": {
                "start": (now + timedelta(days=1)).isoformat(),
                "end":   (now + timedelta(days=flight_days)).isoformat(),
            },
            "kpis": [
                "impressions",
                "click_through_rate",
                "conversion_rate",
                "roas",
            ],
        }
        await self.log_activity(
            "campaign_draft",
            f"Campaign draft: '{name}' on {channels} — ${budget_usd:,.0f} budget",
        )
        return await self.submit_for_approval(
            task_type="marketing_campaign",
            description=f"Launch multi-channel campaign '{name}'",
            payload=payload,
        )

    async def generate_promo_code(
        self,
        discount_pct: float,
        max_uses: int,
        expiry_days: int = 7,
    ) -> dict:
        """Create a promotional discount code (pending Boss approval)."""
        code = f"LUXE{int(discount_pct)}OFF"
        payload = {
            "code": code,
            "discount_pct": discount_pct,
            "max_uses": max_uses,
            "expires_at": (datetime.utcnow() + timedelta(days=expiry_days)).isoformat(),
        }
        await self.log_activity("promo_code_draft", f"Promo code {code}: {discount_pct}% off")
        return await self.submit_for_approval(
            task_type="promo_code",
            description=f"Create promo code {code} ({discount_pct}% off, {max_uses} uses)",
            payload=payload,
        )
