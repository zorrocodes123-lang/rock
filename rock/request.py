from typing import Any, Callable, TypeAlias

class BaseRequest:
    ...

class Order(BaseRequest):
    def __init__(
        self,
        path: str,
        headers: dict[str, str] | None = None,
        body: str | bytes | None = b"",
        method: str = "GET"
    ):
        self.path: str = path
        self.headers: dict[str, str] = headers if headers is not None else {}
        self.body: str | bytes = body if body is not None else b""
        self.method: str = method

