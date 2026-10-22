
from .response import Dish
from .request import Order


class View:
    def __init__(self, Order: Order) -> None:
        self.Order = Order


    def dispatch(self, **parameters: str) -> Dish:
        method = self.Order.method.upper()

        allowed_methods = {
            "GET",
            "POST",
            "PUT",
            "PATCH",
            "DELETE",
            "HEAD",
            "OPTIONS",
        }

        if method not in allowed_methods:
            return Dish(405, {"Allow": ", ".join(sorted(allowed_methods))},
                        "Method not allowed")

        handler = getattr(self, method.lower(), None)

        if handler is None or not callable(handler):
            return Dish(405, {}, "Method not allowed")

        return handler(**parameters)
