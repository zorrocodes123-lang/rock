
from typing import Any, TypeAlias


JSONValue: TypeAlias = (
    str | int | float | bool | None
    | dict[str, Any]
    | list[Any]
)

ResponseBody: TypeAlias = str | bytes | JSONValue


class BaseResponse:
    ...


class Dish(BaseResponse):
    def __init__(
        self,
        status_code: int,
        headers: dict[str, str] | None = None,
        body: ResponseBody = "",
    ) -> None:
        self.status_code: int = status_code
        self.headers: dict[str, str] = headers if headers is not None else {}
        self.body: ResponseBody = body

    def to_dict(self) -> dict[str, Any]:
        return {
            "status_code": self.status_code,
            "headers": self.headers,
            "body": self.body,
        }





class TemplateResponse(Dish):
    def __init__(
        self,
        template_name: str,
        context: dict[str, Any] | None = None,
        status_code: int = 200,
        template_dir: str = "templates",
    ) -> None:
        from .templates import Template

        template = Template(
            template_name=template_name,
            context=context or {},
            template_dir=template_dir,
            status_code=status_code,
        ).render()

        super().__init__(
            status_code=template.status_code,
            headers=template.headers,
            body=template.body,
        )