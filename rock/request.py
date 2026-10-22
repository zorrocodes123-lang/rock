
class BaseRequest:
    """Base class for HTTP requests."""


class Order(BaseRequest):
    """Represents an incoming HTTP request."""

    def __init__(
        self,
        path: str,
        headers: dict[str, str] | None = None,
        body: str | bytes | None = b"",
        method: str = "GET",
    ) -> None:
        if not isinstance(path, str) or not path.startswith("/"):
            raise ValueError("Request path must start with '/'.")

        if not isinstance(method, str):
            raise TypeError("Request method must be a string.")

        if headers is not None and not isinstance(headers, dict):
            raise TypeError("Request headers must be a dictionary.")

        if body is not None and not isinstance(body, (str, bytes)):
            raise TypeError("Request body must be a string or bytes.")

        self.path = path
        self.headers = headers if headers is not None else {}
        self.body = body if body is not None else b""
        self.method = method.upper()
