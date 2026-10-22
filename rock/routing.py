
import re


def compile_route(path: str) -> tuple[re.Pattern, list[str]]:
    if not isinstance(path, str) or not path.startswith("/"):
        raise ValueError("Route paths must start with '/'.")

    parameters = []
    parameter_names = set()
    pattern = "^"

    if path == "/":
        return re.compile(r"^/$"), parameters

    segments = path[1:].split("/")

    if segments[-1] == "":
        segments.pop()

    for segment in segments:
        optional_match = re.fullmatch(r"\[<(\w+)>\]", segment)

        if optional_match:
            name = optional_match.group(1)

            if name in parameter_names:
                raise ValueError(
                    f"Duplicate route parameter: '{name}'."
                )

            parameter_names.add(name)
            parameters.append(name)

            pattern += f"(?:/(?P<{name}>[^/]+))?"
            continue

        pattern += "/"

        def replace_parameter(match: re.Match) -> str:
            name = match.group(1)

            if name in parameter_names:
                raise ValueError(
                    f"Duplicate route parameter: '{name}'."
                )

            parameter_names.add(name)
            parameters.append(name)

            return f"(?P<{name}>[^/]+)"

        parts = re.split(r"(<\w+>)", segment)

        for part in parts:
            match = re.fullmatch(r"<(\w+)>", part)

            if match:
                pattern += replace_parameter(match)
            else:
                pattern += re.escape(part)

    pattern += "/?$"

    return re.compile(pattern), parameters


def _replace_parameter(
    match: re.Match,
    parameters: list[str],
) -> str:
    name = match.group(1)

    if name in parameters:
        raise ValueError(f"Duplicate route parameter: '{name}'.")

    parameters.append(name)
    return f"(?P<{name}>[^/]+)"
