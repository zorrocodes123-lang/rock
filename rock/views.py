
from .response import Dish
from .request import Order


class View:
    def __init__(self, Order: Order) -> None:
        self.Order = Order

    def dispatch(self, **parameters: str) -> Dish:
        handler = getattr(self, self.Order.method.lower(), None)

        if handler is None:
            return Dish(405, {}, "Method not allowed")

        return handler(**parameters)
