
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
import json

from .request import *
from .response import *
from .views import *
from .routing import *


class Rock:
    """Base class for the application."""

    def __init__(self, name: str = "Rock") -> None:
        if not isinstance(name, str):
            raise TypeError("Name must be a string.")

        self.name = name
        self.routes: dict[str, type[View]] = {}
        self.dynamic_routes = []

    def carve(self, routes: dict[str, type[View]]) -> None:
        if not isinstance(routes, dict):
            raise TypeError("Routes must be a dictionary.")

        for path, view in routes.items():
            if not isinstance(path, str) or not path.startswith("/"):
                raise ValueError("Route paths must start with '/'.")

            if not isinstance(view, type) or not issubclass(view, View):
                raise TypeError("Route view must be a View subclass.")

            if "<" not in path and "[" not in path:
                self.routes[path] = view
                continue

            pattern, parameters = compile_route(path)
            self.dynamic_routes = [
                route for route in self.dynamic_routes
                if route[0].pattern != pattern.pattern
            ]
            self.dynamic_routes.append((pattern, parameters, view))

    def resolve(self, path: str):
        if path in self.routes:
            return self.routes[path], {}

        for pattern, parameters, view in self.dynamic_routes:
            match = pattern.fullmatch(path)
            if match:
                return view, {
                    name: match.groupdict().get(name)
                    for name in parameters
                }

        return None, {}

    def make(self, request: Order) -> Dish:
        if not isinstance(request, Order):
            raise TypeError("Request must be an Order.")

        view, parameters = self.resolve(request.path)
        if view is None:
            return Dish(404, {}, "Not Found")

        try:
            return view(request).dispatch(**parameters)
        except Exception:
            return Dish(500, {}, "Internal Server Error")

    def hunt(self, port: int = 8000, host: str = "localhost") -> None:
        app = self

        class Handler(BaseHTTPRequestHandler):
            def _handle(self) -> None:
                try:
                    length = int(self.headers.get("Content-Length", 0))
                    if not 0 <= length <= 10 * 1024 * 1024:
                        self.send_error(400 if length < 0 else 413)
                        return
                except ValueError:
                    self.send_error(400, "Invalid Content-Length")
                    return

                request = Order(
                    urlsplit(self.path).path,
                    dict(self.headers.items()),
                    self.rfile.read(length),
                    "GET" if self.command == "HEAD" else self.command,
                )

                print(f"[{app.name}] {self.command} {request.path}")

                response = app.make(request)
                headers = dict(response.headers)

                if isinstance(response.body, bytes):
                    body = response.body
                elif isinstance(response.body, str):
                    body = response.body.encode("utf-8")
                else:
                    body = json.dumps(response.body).encode("utf-8")
                    if not any(k.lower() == "content-type" for k in headers):
                        headers["Content-Type"] = "application/json; charset=utf-8"

                headers.setdefault("Content-Length", str(len(body)))
                self.send_response(response.status_code)

                for key, value in headers.items():
                    self.send_header(key, value)

                if self.command == "OPTIONS":
                    self.send_header("Allow", "GET, HEAD, POST, PUT, PATCH, DELETE, OPTIONS")

                self.end_headers()

                if self.command not in ("HEAD", "OPTIONS"):
                    self.wfile.write(body)

            do_GET = _handle
            do_HEAD = _handle
            do_POST = _handle
            do_PUT = _handle
            do_PATCH = _handle
            do_DELETE = _handle
            do_OPTIONS = _handle

        try:
            server = ThreadingHTTPServer((host, port), Handler)
            print(f"[{self.name}] Running at http://{host}:{port}")
            server.serve_forever()
        except KeyboardInterrupt:
            print(f"\n[{self.name}] Server stopped.")
        finally:
            if "server" in locals():
                server.server_close()
