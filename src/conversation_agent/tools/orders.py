"""Order tools for the bakery agent."""

from agents import FunctionTool, function_tool

from conversation_agent.logging import log_demo
from conversation_agent.order_store import FulfillmentMethod, OrderStore


def create_update_order_tool(orders: OrderStore) -> FunctionTool:
    """Create a tool backed by the demo order store."""

    @function_tool
    def update_order(
        order_id: str,
        fulfillment_method: FulfillmentMethod,
        delivery_time: str | None = None,
    ) -> dict[str, str | None]:
        """Change whether a bakery order is delivered or collected in store."""

        result = orders.update_order(order_id, fulfillment_method, delivery_time)
        log_demo("ACTION", result)
        return result

    return update_order
