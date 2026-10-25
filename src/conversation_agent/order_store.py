"""
Mock data store for Owl Bakery orders.
In production, this would be backed by a real database or API.
"""

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

FulfillmentMethod = Literal["delivery", "pickup"]
OrderStatus = Literal["confirmed", "preparing", "ready", "out_for_delivery", "completed"]


@dataclass(slots=True)
class OrderItem:
    """One product included in an order."""

    name: str
    quantity: int
    size: str | None = None
    inscription: str | None = None


@dataclass(slots=True)
class Order:
    order_id: str
    customer_phone: str
    items: list[OrderItem]
    order_status: OrderStatus
    fulfillment_method: FulfillmentMethod
    fulfillment_date: str
    delivery_time: str | None = None
    delivery_address: str | None = None
    pickup_location: str | None = None
    live_status: str | None = None


class OrderUpdate(BaseModel):
    """Customer-editable order fields; omitted fields remain unchanged."""

    fulfillment_method: FulfillmentMethod | None = None
    fulfillment_date: str | None = None
    delivery_time: str | None = None
    delivery_address: str | None = None
    inscription: str | None = None

    model_config = ConfigDict(extra="forbid")


class CreateOrderItem(BaseModel):
    """Product details accepted when placing an order."""

    name: str
    quantity: int = Field(ge=1)
    size: str | None = None
    inscription: str | None = None

    model_config = ConfigDict(extra="forbid")


class CreateOrderRequest(BaseModel):
    """Customer-provided details needed to place an order."""

    items: list[CreateOrderItem] = Field(min_length=1)
    fulfillment_method: FulfillmentMethod
    fulfillment_date: str
    delivery_time: str | None = None
    delivery_address: str | None = None

    model_config = ConfigDict(extra="forbid")


def seed_orders(demo_phone: str) -> list[Order]:
    """Create fresh demo orders for lookup, update, and isolation scenarios."""

    return [
        Order(
            order_id="4521",
            customer_phone=demo_phone,
            items=[
                OrderItem(
                    name="Chocolate birthday cake",
                    quantity=1,
                    size="10 inch",
                    inscription="Happy Birthday Maya!",
                )
            ],
            order_status="confirmed",
            fulfillment_method="pickup",
            fulfillment_date="2026-10-25",
            pickup_location="Owl Bakery, 12 High Street",
            live_status="Confirmed and awaiting preparation",
        ),
        Order(
            order_id="4522",
            customer_phone=demo_phone,
            items=[
                OrderItem(
                    name="Owl-themed vanilla cupcakes",
                    quantity=12,
                    inscription="Happy Birthday!",
                )
            ],
            order_status="completed",
            fulfillment_method="delivery",
            fulfillment_date="2026-08-14",
            delivery_time="10:00 AM–12:00 PM",
            delivery_address="18 Willow Lane",
            live_status="Delivered at 11:12 AM",
        ),
        Order(
            order_id="6184",
            customer_phone="+447846889329",
            items=[OrderItem(name="Lemon wedding cake", quantity=1, size="three tier")],
            order_status="out_for_delivery",
            fulfillment_method="delivery",
            fulfillment_date="2026-10-24",
            delivery_time="1:00 PM–3:00 PM",
            delivery_address="7 Meadow Close",
            live_status="Driver is en route; estimated arrival 2:20 PM",
        ),
        Order(
            order_id="7305",
            customer_phone="+15550000003",
            items=[
                OrderItem(
                    name="Vegan carrot cake",
                    quantity=1,
                    size="8 inch",
                    inscription="Congratulations Sam!",
                )
            ],
            order_status="ready",
            fulfillment_method="pickup",
            fulfillment_date="2026-10-24",
            pickup_location="Owl Bakery, 12 High Street",
            live_status="Ready for collection",
        ),
        Order(
            order_id="8416",
            customer_phone="+15550000004",
            items=[
                OrderItem(name="Salted caramel celebration cake", quantity=1, size="10 inch"),
                OrderItem(name="Chocolate owl cookies", quantity=24),
            ],
            order_status="preparing",
            fulfillment_method="delivery",
            fulfillment_date="2026-10-25",
            delivery_time="4:00 PM–6:00 PM",
            delivery_address="25 Orchard View",
            live_status="Cake is being decorated",
        ),
    ]


class OrderStore:
    def __init__(self, orders: Iterable[Order] = ()) -> None:
        self.orders = {order.order_id: order for order in orders}

    def create_order(
        self,
        customer_phone: str,
        request: CreateOrderRequest,
    ) -> dict[str, Any]:
        """Create a confirmed order owned by the current customer."""

        if request.fulfillment_method == "delivery":
            if not request.delivery_time or not request.delivery_address:
                return {
                    "status": "invalid_order",
                    "reason": "Delivery orders require a delivery time and address.",
                }
        elif request.delivery_time or request.delivery_address:
            return {
                "status": "invalid_order",
                "reason": "Delivery details cannot be set on a pickup order.",
            }

        order = Order(
            order_id=self._next_order_id(),
            customer_phone=customer_phone,
            items=[OrderItem(**item.model_dump()) for item in request.items],
            order_status="confirmed",
            fulfillment_method=request.fulfillment_method,
            fulfillment_date=request.fulfillment_date,
            delivery_time=request.delivery_time,
            delivery_address=request.delivery_address,
            pickup_location=(
                "Owl Bakery, 12 High Street" if request.fulfillment_method == "pickup" else None
            ),
            live_status=(
                "Confirmed for collection"
                if request.fulfillment_method == "pickup"
                else "Delivery confirmed and awaiting preparation"
            ),
        )
        self.orders[order.order_id] = order
        return {"status": "created", **asdict(order)}

    def list_customer_orders(self, customer_phone: str) -> dict[str, Any]:
        """Return summaries of orders owned by one customer."""

        matches = [
            order for order in self.orders.values() if order.customer_phone == customer_phone
        ]
        return {
            "status": "found" if matches else "not_found",
            "orders": [self._summary(order) for order in matches],
        }

    def get_order(self, customer_phone: str, order_id: str) -> dict[str, Any]:
        """Return an order only when it belongs to the current customer."""

        order = self._customer_order(customer_phone, order_id)
        if order is None:
            return {"status": "not_found", "order_id": order_id}
        return {"status": "found", **asdict(order)}

    def get_order_status(self, customer_phone: str, order_id: str) -> dict[str, Any]:
        """Return the simulated current fulfillment status for an order."""

        order = self._customer_order(customer_phone, order_id)
        if order is None:
            return {"status": "not_found", "order_id": order_id}
        return {
            "status": "found",
            "order_id": order.order_id,
            "order_status": order.order_status,
            "live_status": order.live_status,
            "fulfillment_method": order.fulfillment_method,
            "delivery_time": order.delivery_time,
        }

    def update_order(
        self,
        customer_phone: str,
        order_id: str,
        update: OrderUpdate,
    ) -> dict[str, Any]:
        """Apply an allowlisted partial update to a customer's order."""

        order = self._customer_order(customer_phone, order_id)
        if order is None:
            return {"status": "not_found", "order_id": order_id}

        changes = update.model_dump(exclude_unset=True)
        if not changes:
            return {"status": "invalid_update", "reason": "No changes were provided."}
        if changes.get("fulfillment_method", "present") is None:
            return {"status": "invalid_update", "reason": "Fulfillment method cannot be empty."}
        if changes.get("fulfillment_date", "present") is None:
            return {"status": "invalid_update", "reason": "Fulfillment date cannot be empty."}
        if "inscription" in changes and not order.items:
            return {"status": "invalid_update", "reason": "The order has no items."}

        fulfillment_method = changes.get("fulfillment_method", order.fulfillment_method)
        delivery_time = changes.get("delivery_time", order.delivery_time)
        delivery_address = changes.get("delivery_address", order.delivery_address)
        if fulfillment_method == "delivery" and not (delivery_time and delivery_address):
            return {
                "status": "invalid_update",
                "reason": "Delivery orders require a delivery time and address.",
            }
        if fulfillment_method == "pickup" and any(
            changes.get(field) is not None for field in ("delivery_time", "delivery_address")
        ):
            return {
                "status": "invalid_update",
                "reason": "Delivery details cannot be set on a pickup order.",
            }

        for field in ("fulfillment_method", "fulfillment_date"):
            if field in changes:
                setattr(order, field, changes[field])

        if "inscription" in changes:
            order.items[0].inscription = changes["inscription"]

        fulfillment_changed = any(
            field in changes
            for field in ("fulfillment_method", "delivery_time", "delivery_address")
        )
        if fulfillment_changed and order.fulfillment_method == "delivery":
            order.delivery_time = delivery_time
            order.delivery_address = delivery_address
            order.pickup_location = None
            order.live_status = "Delivery requested; awaiting bakery confirmation"
        elif fulfillment_changed:
            order.delivery_time = None
            order.delivery_address = None
            order.pickup_location = "Owl Bakery, 12 High Street"
            order.live_status = "Confirmed for collection"
        return {"status": "updated", **asdict(order)}

    def _customer_order(self, customer_phone: str, order_id: str) -> Order | None:
        order = self.orders.get(order_id)
        if order is None or order.customer_phone != customer_phone:
            return None
        return order

    def _next_order_id(self) -> str:
        numeric_ids = [int(order_id) for order_id in self.orders if order_id.isdigit()]
        return str(max(numeric_ids, default=1000) + 1)

    @staticmethod
    def _summary(order: Order) -> dict[str, Any]:
        return {
            "order_id": order.order_id,
            "items": [item.name for item in order.items],
            "order_status": order.order_status,
            "fulfillment_method": order.fulfillment_method,
            "fulfillment_date": order.fulfillment_date,
        }
