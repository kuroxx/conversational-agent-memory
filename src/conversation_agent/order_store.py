"""In-memory order data used by the bakery demo."""

from dataclasses import asdict, dataclass
from typing import Literal

FulfillmentMethod = Literal["delivery", "pickup"]


@dataclass(slots=True)
class Order:
    order_id: str
    fulfillment_method: FulfillmentMethod
    delivery_time: str | None = None


class OrderStore:
    def __init__(self) -> None:
        self.orders = {"4521": Order("4521", "pickup")}

    def update_order(
        self,
        order_id: str,
        fulfillment_method: FulfillmentMethod,
        delivery_time: str | None = None,
    ) -> dict[str, str | None]:
        order = self.orders.get(order_id)
        if order is None:
            return {"status": "not_found", "order_id": order_id}

        order.fulfillment_method = fulfillment_method
        order.delivery_time = delivery_time if fulfillment_method == "delivery" else None
        return {"status": "updated", **asdict(order)}
