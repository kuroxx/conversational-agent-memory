"""Customer-memory retrieval tool for the bakery agent."""

from agents import FunctionTool
from tac import TAC
from tac.models.session import ConversationSession
from tac.tools import create_memory_tool


def create_customer_memory_tool(
    tac: TAC,
    context: ConversationSession,
) -> FunctionTool | None:
    """Create a memory tool when the current session has a known customer."""

    memory_client = tac.conversation_memory_client
    if memory_client is None or not context.profile_id:
        return None

    memory_tool = create_memory_tool(
        memory_client,
        context,
        name="recall_customer_memory",
        description="Retrieve relevant durable memories about the current customer.",
    )
    return memory_tool.to_openai_agents_sdk_tool()
