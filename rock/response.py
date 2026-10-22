
from typing import Any, TypeAlias


JSONValue: TypeAlias = (
    str | int | float | bool | None
    | dict[str, Any]
    | list[Any]
)

ResponseBody: TypeAlias = str | bytes | JSONValue


class BaseResponse:
    """Base class for HTTP responses."""


class Dish(BaseResponse):
    """Represents an HTTP response."""

    def __init__(
        self,
        status_code: int,
        headers: dict[str, str] | None = None,
        body: ResponseBody = "",
    ) -> None:
        if not isinstance(status_code, int) or not 100 <= status_code <= 599:
            raise ValueError("Status code must be between 100 and 599.")

        if headers is not None and not isinstance(headers, dict):
            raise TypeError("Headers must be a dictionary.")

        self.status_code = status_code
        self.headers = headers if headers is not None else {}
        self.body = body

    def to_dict(self) -> dict[str, Any]:
        return {
            "status_code": self.status_code,
            "headers": self.headers,
            "body": self.body,
        }


class Render(Dish):
    """Renders an HTML template into a response."""

    def __init__(
        self,
        template_name: str,
        context: dict[str, Any] | None = None,
        status_code: int = 200,
        template_dir: str = "templates",
    ) -> None:
        from .templates import Template

        response = Template(
            template_name,
            context,
            template_dir,
            status_code,
        ).render()

        super().__init__(
            response.status_code,
            response.headers,
            response.body,
        )


class Redirect(Dish):
    """Redirects the client to another path."""

    def __init__(self, path: str, status_code: int = 302) -> None:
        if not isinstance(path, str) or not path:
            raise ValueError("Redirect path must be a non-empty string.")

        if status_code not in (301, 302, 303, 307, 308):
            raise ValueError("Invalid redirect status code.")

        super().__init__(status_code, {"Location": path}, "")
