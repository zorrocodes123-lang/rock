
from typing import Any, TypeAlias


JSONValue: TypeAlias = (
    str | int | float | bool | None
    | dict[str, Any]
    | list[Any]
)

ResponseBody: TypeAlias = str | bytes | JSONValue


class BaseResponse:
    """Base class for HTTP responses."""


class Codes:
    """HTTP status codes."""

    CONTINUE = 100
    SWITCHING_PROTOCOLS = 101
    PROCESSING = 102
    EARLY_HINTS = 103

    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204

    MOVED_PERMANENTLY = 301
    FOUND = 302
    SEE_OTHER = 303
    NOT_MODIFIED = 304
    TEMPORARY_REDIRECT = 307
    PERMANENT_REDIRECT = 308

    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    NOT_ACCEPTABLE = 406
    REQUEST_TIMEOUT = 408
    CONFLICT = 409
    GONE = 410
    CONTENT_TOO_LARGE = 413
    UNSUPPORTED_MEDIA_TYPE = 415
    IM_A_TEAPOT = 418
    UNPROCESSABLE_CONTENT = 422
    TOO_MANY_REQUESTS = 429

    INTERNAL_SERVER_ERROR = 500
    NOT_IMPLEMENTED = 501
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504


class Headers:
    """Common HTTP headers."""

    @staticmethod
    def CONTENT_JSON() -> dict[str, str]:
        return {"Content-Type": "application/json; charset=utf-8"}

    @staticmethod
    def CONTENT_TEXT() -> dict[str, str]:
        return {"Content-Type": "text/plain; charset=utf-8"}

    @staticmethod
    def CONTENT_HTML() -> dict[str, str]:
        return {"Content-Type": "text/html; charset=utf-8"}

    @staticmethod
    def CONTENT_CSS() -> dict[str, str]:
        return {"Content-Type": "text/css; charset=utf-8"}

    @staticmethod
    def CONTENT_JAVASCRIPT() -> dict[str, str]:
        return {"Content-Type": "text/javascript; charset=utf-8"}

    @staticmethod
    def CONTENT_XML() -> dict[str, str]:
        return {"Content-Type": "application/xml; charset=utf-8"}

    @staticmethod
    def CONTENT_BINARY() -> dict[str, str]:
        return {"Content-Type": "application/octet-stream"}

    @staticmethod
    def CONTENT_PDF() -> dict[str, str]:
        return {"Content-Type": "application/pdf"}

    @staticmethod
    def CONTENT_PNG() -> dict[str, str]:
        return {"Content-Type": "image/png"}

    @staticmethod
    def CONTENT_JPEG() -> dict[str, str]:
        return {"Content-Type": "image/jpeg"}

    @staticmethod
    def LOCATION(path: str) -> dict[str, str]:
        return {"Location": path}


class Dish(BaseResponse):
    """Represents an HTTP response."""

    def __init__(
        self,
        status_code: int,
        headers: dict[str, str] | None = None,
        body: ResponseBody = "",
    ) -> None:
        if not isinstance(status_code, int) or isinstance(status_code, bool):
            raise TypeError("Status code must be an integer.")

        if not 100 <= status_code <= 599:
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


class Response(BaseResponse):
    """Helper methods for creating HTTP responses."""

    @staticmethod
    def text(text: str) -> Dish:
        return Dish(
            Codes.OK,
            Headers.CONTENT_TEXT(),
            text,
        )

    @staticmethod
    def json(data: dict[str, Any]) -> Dish:
        return Dish(
            Codes.OK,
            Headers.CONTENT_JSON(),
            data,
        )

    @staticmethod
    def render(
        path: str,
        template_folder: str = "templates",
        context: dict[str, Any] | None = None,
    ) -> Dish:
        from .templates import Template

        response = Template(
            path,
            context,
            template_folder,
            Codes.OK,
        ).render()

        return Dish(
            response.status_code,
            response.headers,
            response.body,
        )

    @staticmethod
    def redirect(
        path: str,
        status_code: int = Codes.FOUND,
    ) -> Dish:
        if not isinstance(path, str) or not path:
            raise ValueError("Redirect path must be a non-empty string.")

        if status_code not in (
            Codes.MOVED_PERMANENTLY,
            Codes.FOUND,
            Codes.SEE_OTHER,
            Codes.TEMPORARY_REDIRECT,
            Codes.PERMANENT_REDIRECT,
        ):
            raise ValueError("Invalid redirect status code.")

        return Dish(
            status_code,
            Headers.LOCATION(path),
            "",
        )
