
import ast
import re
from html import escape
from pathlib import Path
from typing import Any

from .response import Dish


TOKEN_PATTERN = re.compile(r"({{.*?}}|{%.*?%})", re.DOTALL)
BLOCK_PATTERN = re.compile(
    r"{%\s*block\s+(\w+)\s*%}(.*?){%\s*endblock\s*%}",
    re.DOTALL,
)


class Template:
    def __init__(
        self,
        template_name: str,
        context: dict[str, Any] | None = None,
        template_dir: str = "templates",
        status_code: int = 200,
    ) -> None:
        self.template_name = template_name
        self.context = context or {}
        self.template_dir = Path(template_dir).resolve()
        self.status_code = status_code
        self._overrides: dict[str, str] = {}

    def render(self) -> Dish:
        body = self._render_template(
            self.template_name, self.context, {}, set()
        )
        return Dish(
            self.status_code,
            {"Content-Type": "text/html; charset=utf-8"},
            body,
        )

    def _render_template(
        self,
        name: str,
        context: dict[str, Any],
        overrides: dict[str, str],
        seen: set[str],
    ) -> str:
        path = (self.template_dir / name).resolve()

        if not path.is_relative_to(self.template_dir):
            raise ValueError("Template path escapes template directory.")

        if name in seen:
            raise ValueError("Circular template inheritance detected.")

        source = path.read_text(encoding="utf-8")
        seen = seen | {name}

        parent = re.search(
            r'{%\s*extends\s+["\'](.+?)["\']\s*%}', source
        )

        if parent:
            blocks = {
                match.group(1): match.group(2)
                for match in BLOCK_PATTERN.finditer(source)
            }
            return self._render_template(
                parent.group(1), context, {**overrides, **blocks}, seen
            )

        self._overrides = overrides
        nodes, index, ending = self._parse(
            TOKEN_PATTERN.split(source), 0, set()
        )

        if ending is not None or index != len(TOKEN_PATTERN.split(source)):
            raise ValueError("Unexpected template closing tag.")

        return self._render_nodes(nodes, context)

    def _parse(
        self,
        tokens: list[str],
        index: int,
        stops: set[str],
    ) -> tuple[list, int, str | None]:
        nodes = []

        while index < len(tokens):
            token = tokens[index]

            if token.startswith("{{"):
                expression = token[2:-2].strip()
                if not expression:
                    raise ValueError("Empty template expression.")
                nodes.append(("variable", expression))
                index += 1
                continue

            if not token.startswith("{%"):
                nodes.append(("text", token))
                index += 1
                continue

            tag = token[2:-2].strip()
            parts = tag.split(maxsplit=1)

            if not parts:
                raise ValueError("Empty template tag.")

            command = parts[0]

            if command in stops:
                return nodes, index + 1, tag

            if command == "if":
                condition = tag[3:].strip()
                if not condition:
                    raise ValueError("Missing if condition.")

                yes, index, ending = self._parse(
                    tokens, index + 1, {"else", "endif"}
                )
                no = []

                if ending is None:
                    raise ValueError("Missing 'endif' tag.")

                if ending.split(maxsplit=1)[0] == "else":
                    no, index, ending = self._parse(
                        tokens, index, {"endif"}
                    )

                if ending != "endif":
                    raise ValueError("Missing 'endif' tag.")

                nodes.append(("if", condition, yes, no))
                continue

            if command == "for":
                match = re.fullmatch(r"for\s+(\w+)\s+in\s+(.+)", tag)
                if not match:
                    raise ValueError(f"Invalid for tag: {tag}")

                variable, expression = match.groups()
                body, index, ending = self._parse(
                    tokens, index + 1, {"endfor"}
                )

                if ending != "endfor":
                    raise ValueError("Missing 'endfor' tag.")

                nodes.append(("for", variable, expression, body))
                continue

            if command == "block":
                if len(parts) != 2 or not re.fullmatch(r"\w+", parts[1]):
                    raise ValueError(f"Invalid block tag: {tag}")

                body, index, ending = self._parse(
                    tokens, index + 1, {"endblock"}
                )

                if ending != "endblock":
                    raise ValueError("Missing 'endblock' tag.")

                nodes.append(("block", parts[1], body))
                continue

            raise ValueError(f"Unknown template tag: {tag}")

        return nodes, index, None

    def _render_nodes(self, nodes: list, context: dict[str, Any]) -> str:
        output = []

        for node in nodes:
            kind = node[0]

            if kind == "text":
                output.append(node[1])

            elif kind == "variable":
                value = self._evaluate(node[1], context)
                output.append(
                    escape(str(value), quote=True)
                    if value is not None else ""
                )

            elif kind == "if":
                _, condition, yes, no = node
                branch = yes if self._evaluate(condition, context) else no
                output.append(self._render_nodes(branch, context))

            elif kind == "for":
                _, variable, expression, body = node
                values = self._evaluate(expression, context)

                if values is not None:
                    for value in values:
                        local = {**context, variable: value}
                        output.append(self._render_nodes(body, local))

            elif kind == "block":
                _, name, body = node

                if name in self._overrides:
                    tokens = TOKEN_PATTERN.split(self._overrides[name])
                    child, index, ending = self._parse(tokens, 0, set())

                    if ending is not None or index != len(tokens):
                        raise ValueError("Invalid block content.")

                    output.append(self._render_nodes(child, context))
                else:
                    output.append(self._render_nodes(body, context))

        return "".join(output)

    def _evaluate(self, expression: str, context: dict[str, Any]) -> Any:
        return self._eval_node(ast.parse(expression, mode="eval").body, context)

    def _eval_node(self, node: ast.AST, context: dict[str, Any]) -> Any:
        if isinstance(node, ast.Constant):
            return node.value

        if isinstance(node, ast.Name):
            return context.get(node.id)

        if isinstance(node, ast.Attribute):
            if node.attr.startswith("_"):
                raise ValueError("Private attributes are not allowed.")

            value = self._eval_node(node.value, context)

            if isinstance(value, dict):
                return value.get(node.attr)

            return getattr(value, node.attr, None) if value is not None else None

        if isinstance(node, ast.Subscript):
            value = self._eval_node(node.value, context)
            key = self._eval_node(node.slice, context)

            try:
                return value[key]
            except (KeyError, IndexError, TypeError):
                return None

        if isinstance(node, (ast.List, ast.Tuple)):
            values = [self._eval_node(item, context) for item in node.elts]
            return values if isinstance(node, ast.List) else tuple(values)

        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            return not self._eval_node(node.operand, context)

        if isinstance(node, ast.BoolOp):
            result = self._eval_node(node.values[0], context)

            for item in node.values[1:]:
                if isinstance(node.op, ast.And):
                    if not result:
                        return result
                elif isinstance(node.op, ast.Or):
                    if result:
                        return result
                else:
                    raise ValueError("Unsupported Boolean operator.")

                result = self._eval_node(item, context)

            return result

        if isinstance(node, ast.Compare):
            left = self._eval_node(node.left, context)

            for operator, comparator in zip(node.ops, node.comparators):
                right = self._eval_node(comparator, context)

                if isinstance(operator, ast.Eq):
                    result = left == right
                elif isinstance(operator, ast.NotEq):
                    result = left != right
                elif isinstance(operator, ast.Lt):
                    result = left < right
                elif isinstance(operator, ast.LtE):
                    result = left <= right
                elif isinstance(operator, ast.Gt):
                    result = left > right
                elif isinstance(operator, ast.GtE):
                    result = left >= right
                elif isinstance(operator, ast.In):
                    result = left in right
                elif isinstance(operator, ast.NotIn):
                    result = left not in right
                else:
                    raise ValueError("Unsupported comparison operator.")

                if not result:
                    return False

                left = right

            return True

        raise ValueError(f"Unsupported expression: {ast.dump(node)}")
