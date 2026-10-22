
from .response import Dish
from .request import Order


class View:
    def __init__(self, request: Order) -> None:
        self.request = request

    def dispatch(self, **parameters: str) -> Dish:
        method = self.request.method.upper()
        allowed = {"GET", "POST", "PUT", "PATCH", "DELETE"}
        methods = allowed | {"HEAD", "OPTIONS"}

        if method not in methods:
            return Dish(405, {"Allow": ", ".join(sorted(methods)),}, "Method Not Allowed")

        if method == "OPTIONS":
            return Dish(204, {"Allow": ", ".join(sorted(methods))})

        handler = getattr(self, method.lower(), None)

        if method == "HEAD" and not callable(handler):
            handler = getattr(self, "get", None)

        if not callable(handler):
            return Dish(405, {"Allow": ", ".join(sorted(methods))}, "Method Not Allowed")

        return handler(**parameters)
