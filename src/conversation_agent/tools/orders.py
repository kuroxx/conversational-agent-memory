"""Order tools for the bakery agent."""

from typing import Any

from agents import FunctionTool, function_tool

from conversation_agent.logging import log_demo
from conversation_agent.order_store import CreateOrderRequest, OrderStore, OrderUpdate


def create_order_tools(orders: OrderStore, customer_phone: str) -> list[FunctionTool]:
    """Create customer-scoped tools backed by the demo order store."""

    @function_tool
    def create_order(request: CreateOrderRequest) -> dict[str, Any]:
        """Place a bakery order for the current customer."""

        result = orders.create_order(customer_phone, request)
        log_demo("ACTION", result)
        return result

    @function_tool
    def lookup_orders() -> dict[str, Any]:
        """Find bakery orders belonging to the current customer."""

        result = orders.list_customer_orders(customer_phone)
        log_demo("ORDER LOOKUP", result)
        return result

    @function_tool
    def lookup_order(order_id: str) -> dict[str, Any]:
        """Get product and fulfillment details for one of the customer's orders."""

        result = orders.get_order(customer_phone, order_id)
        log_demo("ORDER LOOKUP", result)
        return result

    @function_tool
    def get_order_status(order_id: str) -> dict[str, Any]:
        """Get the current live fulfillment status of a customer's order."""

        result = orders.get_order_status(customer_phone, order_id)
        log_demo("LIVE ORDER STATUS", result)
        return result

    @function_tool
    def update_order(
        order_id: str,
        update: OrderUpdate,
    ) -> dict[str, Any]:
        """Update selected fulfillment details or the inscription on a customer order."""

        result = orders.update_order(customer_phone, order_id, update)
        log_demo("ACTION", result)
        return result

    return [create_order, lookup_orders, lookup_order, get_order_status, update_order]
