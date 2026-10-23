"""Compose the tools available to each bakery-agent session."""

from agents import FunctionTool
from tac import TAC
from tac.models.session import ConversationSession

from conversation_agent.order_store import OrderStore
from conversation_agent.tools.knowledge import create_bakery_knowledge_tool
from conversation_agent.tools.memory import create_customer_memory_tool
from conversation_agent.tools.messaging import create_send_sms_tool
from conversation_agent.tools.orders import create_update_order_tool


class ToolProvider:
    """Combine shared action tools with session-specific retrieval tools."""

    def __init__(self, tac: TAC) -> None:
        self.tac = tac
        orders = OrderStore()
        self.action_tools = [
            create_update_order_tool(orders),
            create_send_sms_tool(),
        ]

    async def for_session(self, context: ConversationSession) -> list[FunctionTool]:
        """Return all tools available in the current conversation."""

        memory_tool = create_customer_memory_tool(self.tac, context)
        knowledge_tool = await create_bakery_knowledge_tool(self.tac)
        retrieval_tools = [tool for tool in (memory_tool, knowledge_tool) if tool is not None]
        return [*self.action_tools, *retrieval_tools]
