
import ast
import re

from pathlib import Path
from typing import Any

from .response import Dish


TOKEN_PATTERN = re.compile(
    r"({{.*?}}|{%.*?%})",
    re.DOTALL,
)

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
        self.context = context if context is not None else {}
        self.template_dir = Path(template_dir)
        self.status_code = status_code

    def render(self) -> Dish:
        body = self._render_template(
            self.template_name,
            self.context,
            {},
            set(),
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
        if name in seen:
            raise ValueError("Circular template inheritance detected.")

        seen = seen | {name}
        path = self.template_dir / name
        source = path.read_text(encoding="utf-8")

        extends_match = re.search(
            r'{%\s*extends\s+["\'](.+?)["\']\s*%}',
            source,
        )

        if extends_match:
            child_blocks = {
                match.group(1): match.group(2)
                for match in BLOCK_PATTERN.finditer(source)
            }

            return self._render_template(
                extends_match.group(1),
                context,
                {**overrides, **child_blocks},
                seen,
            )

        self._overrides = overrides
        tokens = TOKEN_PATTERN.split(source)

        nodes, index, _ = self._parse(tokens, 0, set())

        return self._render_nodes(nodes, context)

    def _parse(self, tokens, index, stops):
        nodes = []

        while index < len(tokens):
            token = tokens[index]

            if token.startswith("{{"):
                nodes.append(("variable", token[2:-2].strip()))
                index += 1
                continue

            if not token.startswith("{%"):
                nodes.append(("text", token))
                index += 1
                continue

            tag = token[2:-2].strip()
            command = tag.split(maxsplit=1)[0]

            if command in stops:
                return nodes, index + 1, tag

            if command == "if":
                condition = tag[3:].strip()
                yes, index, ending = self._parse(
                    tokens, index + 1, {"else", "endif"}
                )
                no = []

                if ending and ending.startswith("else"):
                    no, index, _ = self._parse(
                        tokens, index, {"endif"}
                    )

                nodes.append(("if", condition, yes, no))
                continue

            if command == "for":
                match = re.fullmatch(
                    r"for\s+(\w+)\s+in\s+(.+)",
                    tag,
                )
                if not match:
                    raise ValueError(f"Invalid for tag: {tag}")

                variable, expression = match.groups()
                body, index, _ = self._parse(
                    tokens, index + 1, {"enfor", "endfor"}
                )
                nodes.append(("for", variable, expression, body))
                continue

            if command == "block":
                block_name = tag.split(maxsplit=1)[1]
                body, index, _ = self._parse(
                    tokens, index + 1, {"endblock"}
                )
                nodes.append(("block", block_name, body))
                continue

            raise ValueError(f"Unknown template tag: {tag}")

        return nodes, index, None

    def _render_nodes(self, nodes, context):
        output = []

        for node in nodes:
            kind = node[0]

            if kind == "text":
                output.append(node[1])

            elif kind == "variable":
                value = self._evaluate(node[1], context)
                output.append(str(value if value is not None else ""))

            elif kind == "if":
                _, condition, yes, no = node
                branch = yes if self._evaluate(condition, context) else no
                output.append(self._render_nodes(branch, context))

            elif kind == "for":
                _, variable, expression, body = node
                values = self._evaluate(expression, context)

                if values is not None:
                    for value in values:
                        local_context = {**context, variable: value}
                        output.append(
                            self._render_nodes(body, local_context)
                        )

            elif kind == "block":
                _, name, body = node

                if name in self._overrides:
                    child_source = self._overrides[name]
                    child_tokens = TOKEN_PATTERN.split(child_source)
                    child_nodes, _, _ = self._parse(
                        child_tokens, 0, set()
                    )
                    output.append(
                        self._render_nodes(child_nodes, context)
                    )
                else:
                    output.append(self._render_nodes(body, context))

        return "".join(output)

    def _evaluate(self, expression: str, context: dict[str, Any]):
        tree = ast.parse(expression, mode="eval")
        return self._eval_node(tree.body, context)

    def _eval_node(self, node, context):
        if isinstance(node, ast.Constant):
            return node.value

        if isinstance(node, ast.Name):
            return context.get(node.id)

        if isinstance(node, ast.Attribute):
            value = self._eval_node(node.value, context)

            if isinstance(value, dict):
                return value.get(node.attr)

            if node.attr.startswith("_"):
                raise ValueError("Private attributes are not allowed.")

            return getattr(value, node.attr, None) if value is not None else None

        if isinstance(node, ast.Subscript):
            value = self._eval_node(node.value, context)
            key = self._eval_node(node.slice, context)
            return value[key]

        if isinstance(node, (ast.List, ast.Tuple)):
            values = [self._eval_node(item, context) for item in node.elts]
            return values if isinstance(node, ast.List) else tuple(values)

        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            return not self._eval_node(node.operand, context)

        if isinstance(node, ast.BoolOp):
            values = [self._eval_node(v, context) for v in node.values]

            if isinstance(node.op, ast.And):
                return all(values)

            if isinstance(node.op, ast.Or):
                return any(values)

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

        raise ValueError(
            f"Unsupported expression: {ast.dump(node)}"
        )
