
import re


def compile_route(path: str) -> tuple[re.Pattern[str], list[str]]:
    if not isinstance(path, str) or not path.startswith("/"):
        raise ValueError("Route paths must start with '/'.")

    if path == "/":
        return re.compile(r"^/$"), []

    parameters: list[str] = []
    names: set[str] = set()
    pattern = "^"
    segments = path[1:].split("/")

    if segments[-1] == "":
        segments.pop()

    def add_parameter(name: str) -> str:
        if name in names:
            raise ValueError(f"Duplicate route parameter: '{name}'.")

        names.add(name)
        parameters.append(name)
        return f"(?P<{name}>[^/]+)"

    for segment in segments:
        optional = re.fullmatch(r"\[<(\w+)>\]", segment)

        if optional:
            name = optional.group(1)
            pattern += f"(?:/{add_parameter(name)})?"
            continue

        pattern += "/"

        parts = re.split(r"(<\w+>)", segment)

        for part in parts:
            match = re.fullmatch(r"<(\w+)>", part)

            if match:
                pattern += add_parameter(match.group(1))
            else:
                pattern += re.escape(part)

    return re.compile(pattern + "/?$"), parameters
