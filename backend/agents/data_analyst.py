"""
Agent 09 – Data Analyst
(Sales trend, cohort, inventory, marketing ROI)
"""
from datetime import datetime
from typing import Optional
from .abstract_agent import SpecializedAgentClient


ANALYSIS_TYPES = [
    "sales_trend",
    "cohort",
    "inventory",
    "marketing_roi",
    "top_products",
    "customer_ltv",
]


class DataAnalyst(SpecializedAgentClient):
    def __init__(self, boss_api_url: str = None):
        super().__init__("09", boss_api_url)

    async def run_analysis(
        self,
        analysis_type: str,
        params: Optional[dict] = None,
    ) -> dict:
        """
        Queue an analytics job.
        The executor stores the request in analytics_results; a background worker
        (or cron) runs the query and writes the result back.
        """
        if analysis_type not in ANALYSIS_TYPES:
            raise ValueError(
                f"Unknown analysis_type '{analysis_type}'. "
                f"Valid: {ANALYSIS_TYPES}"
            )

        payload = {
            "analysis_type": analysis_type,
            "params": params or {},
            "requested_at": datetime.utcnow().isoformat(),
        }
        await self.log_activity(
            "analysis_requested",
            f"Analysis requested: {analysis_type}",
            details=params,
        )
        return await self.submit_for_approval(
            task_type="analysis_request",
            description=f"Run {analysis_type} analysis",
            payload=payload,
        )

    async def schedule_recurring(
        self,
        analysis_type: str,
        frequency: str = "daily",
        params: Optional[dict] = None,
    ) -> dict:
        """Schedule a recurring analysis job (pending Boss approval)."""
        payload = {
            "analysis_type": analysis_type,
            "frequency": frequency,
            "params": params or {},
        }
        await self.log_activity(
            "recurring_analysis_scheduled",
            f"Scheduled {frequency} {analysis_type}",
        )
        return await self.submit_for_approval(
            task_type="recurring_analysis",
            description=f"Schedule {frequency} {analysis_type} analysis",
            payload=payload,
        )
