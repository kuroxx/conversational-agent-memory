"""Compose the tools available to each bakery-agent session."""

import os

from agents import FunctionTool
from tac import TAC
from tac.models.session import ConversationSession

from conversation_agent.order_store import OrderStore, seed_orders
from conversation_agent.tools.knowledge import create_bakery_knowledge_tool
from conversation_agent.tools.memory import create_customer_memory_tool
from conversation_agent.tools.messaging import create_send_sms_tool
from conversation_agent.tools.orders import create_order_tools


class ToolProvider:
    """Combine shared action tools with session-specific retrieval tools."""

    def __init__(self, tac: TAC) -> None:
        self.tac = tac
        demo_phone = os.getenv("DEMO_CUSTOMER_PHONE", "+15558675310")
        self.orders = OrderStore(seed_orders(demo_phone))
        self.messaging_tools = [create_send_sms_tool()]

    async def for_session(self, context: ConversationSession) -> list[FunctionTool]:
        """Return all tools available in the current conversation."""

        memory_tool = create_customer_memory_tool(self.tac, context)
        knowledge_tool = await create_bakery_knowledge_tool(self.tac)
        retrieval_tools = [tool for tool in (memory_tool, knowledge_tool) if tool is not None]
        customer_phone = _customer_phone(context)
        order_tools = create_order_tools(self.orders, customer_phone) if customer_phone else []
        return [*self.messaging_tools, *order_tools, *retrieval_tools]


def _customer_phone(context: ConversationSession) -> str | None:
    """Resolve a verified customer phone without exposing identity to the model."""

    if not context.profile_id:
        return None

    if context.profile:
        contact = context.profile.traits.get("Contact", {})
        if isinstance(contact, dict) and isinstance(contact.get("phone"), str):
            return contact["phone"]

    return context.author_info.address if context.author_info else None
