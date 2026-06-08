"""
Agent 10 – Customer Experience
(Support tickets, returns, size questions)
"""
from typing import Optional
from .abstract_agent import SpecializedAgentClient


class CustomerExperienceAgent(SpecializedAgentClient):
    def __init__(self, boss_api_url: str = None):
        super().__init__("10", boss_api_url)

    async def generate_support_response(
        self,
        ticket_id: int,
        issue_type: str,
        customer_tone: str = "frustrated",
        context: Optional[dict] = None,
    ) -> dict:
        """
        Draft a support response for a ticket (pending Boss approval).
        After approval the executor calls the LLM (services/ai_text.py) to fill
        `suggested_response`, then stores it as a CXResponse record.
        Optionally auto-sends via a help-desk API if configured.
        """
        payload = {
            "ticket_id": ticket_id,
            "issue_type": issue_type,
            "customer_tone": customer_tone,
            "context": context or {},
            "suggested_response": "",   # filled by executor
        }
        await self.log_activity(
            "cx_response_draft",
            f"Drafting response for ticket #{ticket_id} ({issue_type})",
        )
        return await self.submit_for_approval(
            task_type="cx_response",
            description=f"Draft CX response for ticket {ticket_id}",
            payload=payload,
        )

    async def process_return(
        self,
        order_id: int,
        reason: str,
        items: Optional[list] = None,
    ) -> dict:
        """Initiate a return/refund workflow (pending Boss approval)."""
        payload = {
            "order_id": order_id,
            "reason": reason,
            "items": items or [],
        }
        await self.log_activity("return_initiated", f"Return for order #{order_id}: {reason}")
        return await self.submit_for_approval(
            task_type="return_request",
            description=f"Process return for order #{order_id}",
            payload=payload,
        )

    async def send_proactive_followup(
        self,
        customer_ids: list,
        message_template: str,
        trigger_event: str = "post_purchase",
    ) -> dict:
        """Send proactive outreach to customers (pending Boss approval)."""
        payload = {
            "customer_ids": customer_ids,
            "message_template": message_template,
            "trigger_event": trigger_event,
        }
        await self.log_activity(
            "proactive_followup",
            f"Proactive {trigger_event} message to {len(customer_ids)} customer(s)",
        )
        return await self.submit_for_approval(
            task_type="cx_outreach",
            description=f"Send {trigger_event} follow-up to {len(customer_ids)} customer(s)",
            payload=payload,
        )
