
import re


def compile_route(path: str):
    parameters = []

    optional_match = re.search(r"\[<(\w+)>\]", path)
    optional_parameter = None

    if optional_match:
        optional_parameter = optional_match.group(1)
        path = path[:optional_match.start()] + path[optional_match.end():]

    pattern = re.sub(
        r"<(\w+)>",
        lambda match: _replace_parameter(match, parameters),
        path,
    )

    if optional_parameter:
        parameters.append(optional_parameter)
        pattern = pattern.rstrip("/") + (
            f"(?:/(?P<{optional_parameter}>[^/]+))?"
        )

    return re.compile(f"^{pattern}/?$"), parameters


def _replace_parameter(match, parameters: list[str]) -> str:
    name = match.group(1)
    parameters.append(name)
    return f"(?P<{name}>[^/]+)"
