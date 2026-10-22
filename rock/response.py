
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
        # 1xx — Informational

class Codes:
    @staticmethod
    def CONTINUE(): return 100

    @staticmethod
    def SWITCHING_PROTOCOLS(): return 101

    @staticmethod
    def PROCESSING(): return 102

    @staticmethod
    def EARLY_HINTS(): return 103

    # 2xx — Success

    @staticmethod
    def OK(): return 200

    @staticmethod
    def CREATED(): return 201

    @staticmethod
    def ACCEPTED(): return 202

    @staticmethod
    def NO_CONTENT(): return 204

    # 3xx — Redirection

    @staticmethod
    def MOVED_PERMANENTLY(): return 301

    @staticmethod
    def FOUND(): return 302

    @staticmethod
    def SEE_OTHER(): return 303

    @staticmethod
    def NOT_MODIFIED(): return 304

    @staticmethod
    def TEMPORARY_REDIRECT(): return 307

    @staticmethod
    def PERMANENT_REDIRECT(): return 308

    # 4xx — Client Errors

    @staticmethod
    def BAD_REQUEST(): return 400

    @staticmethod
    def UNAUTHORIZED(): return 401

    @staticmethod
    def FORBIDDEN(): return 403

    @staticmethod
    def NOT_FOUND(): return 404

    @staticmethod
    def METHOD_NOT_ALLOWED(): return 405

    @staticmethod
    def NOT_ACCEPTABLE(): return 406

    @staticmethod
    def REQUEST_TIMEOUT(): return 408

    @staticmethod
    def CONFLICT(): return 409

    @staticmethod
    def GONE(): return 410

    @staticmethod
    def CONTENT_TOO_LARGE(): return 413

    @staticmethod
    def UNSUPPORTED_MEDIA_TYPE(): return 415

    @staticmethod
    def IM_A_TEAPOT(): return 418

    @staticmethod
    def UNPROCESSABLE_CONTENT(): return 422

    @staticmethod
    def TOO_MANY_REQUESTS(): return 429

    # 5xx — Server Errors

    @staticmethod
    def INTERNAL_SERVER_ERROR(): return 500

    @staticmethod
    def NOT_IMPLEMENTED(): return 501

    @staticmethod
    def BAD_GATEWAY(): return 502

    @staticmethod
    def SERVICE_UNAVAILABLE(): return 503

    @staticmethod
    def GATEWAY_TIMEOUT(): return 504

class Headers:
    """Common HTTP headers for Rocks."""

    @staticmethod
    def CONTENT_JSON(): return {"Content-Type": "application/json; charset=utf-8"}

    @staticmethod
    def CONTENT_TEXT(): return {"Content-Type": "text/plain; charset=utf-8"}

    @staticmethod
    def CONTENT_HTML(): return {"Content-Type": "text/html; charset=utf-8"}

    @staticmethod
    def CONTENT_CSS(): return {"Content-Type": "text/css; charset=utf-8"}

    @staticmethod
    def CONTENT_JAVASCRIPT(): return {"Content-Type": "text/javascript; charset=utf-8"}

    @staticmethod
    def CONTENT_XML(): return {"Content-Type": "application/xml; charset=utf-8"}

    @staticmethod
    def CONTENT_BINARY(): return {"Content-Type": "application/octet-stream"}

    @staticmethod
    def CONTENT_PDF(): return {"Content-Type": "application/pdf"}

    @staticmethod
    def CONTENT_PNG(): return {"Content-Type": "image/png"}

    @staticmethod
    def CONTENT_JPEG(): return {"Content-Type": "image/jpeg"}

    @staticmethod
    def LOCATION(path: str): return {"Location":path}

class Response(BaseResponse):

    @staticmethod
    def text(text: str) -> Dish:
        return Dish(
            Codes.OK,
            Headers.CONTENT_TEXT(),
            text,
        )

    @staticmethod
    def json(json: dict[str, Any]) -> Dish:
        return Dish(
            Codes.OK,
            Headers.CONTENT_JSON(),
            json,
        )

    @staticmethod
    def render(
        path: str,
        template_folder: str = "templates",
        context: dict[str, Any] | None = None,
    ) -> Dish:
        return Render(
            path,
            context=context,
            template_dir=template_folder,
            status_code=Codes.OK,
        )
    @staticmethod
    def redirect(path: str):
        return Dish(Codes.FOUND, Headers.LOCATION(path), b"")

