from typing import Any, Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from .request  import *
from .response import *
from .views import *
from .routing import *
from urllib.parse import urlsplit
import json

class Rock:
    '''Base class for the application.'''
    def __init__(self, name: str = "Rock"):
        '''Initialize the application with a name'''
        assert isinstance(name, str), "Name should be a string."
        self.name: str = name
        self.routes: dict[str, type[View]] = {}
        self.dynamic_routes = []

    def carve(self, routes: dict[str, type[View]]) -> None:
        if not isinstance(routes, dict):
            raise TypeError("Routes must be a dictionary.")

        for path, view in routes.items():
            if not isinstance(path, str):
                raise TypeError("Route path must be a string.")

            if not isinstance(view, type) or not issubclass(view, View):
                raise TypeError("Route view must be a View subclass.")

            if not path.startswith("/"):
                raise ValueError("Route path must start with '/'.")

            if "<" not in path:
                self.routes[path] = view
                continue

            pattern, parameters = compile_route(path)

            self.dynamic_routes.append(
                (pattern, parameters, view)
            )

    def resolve(self, path: str):
        if path in self.routes:
            return self.routes[path], {}

        for pattern, parameters, view in self.dynamic_routes:
            match = pattern.fullmatch(path)

            if match:
                values = match.groupdict()

                for name in parameters:
                    values.setdefault(name, None)

                return view, values

        return None, {}
    def make(self, request: Order) -> Dish:
        assert isinstance(request, Order), "Request must be of type Order."

        view, parameters = self.resolve(request.path)

        if view is None:
            return Dish(404, {}, "Not Found")

        return view(request).dispatch(**parameters)
    def hunt(self, port: int = 8000, host: str = "localhost") -> None:
        app = self
        try:
            class Handler(BaseHTTPRequestHandler):
                def _handle(self):
                    try:
                        length = int(self.headers.get("Content-Length", 0))
                    except ValueError:
                        self.send_error(400, "Invalid Content-Length")
                        return

                    if length < 0:
                        self.send_error(400, "Invalid Content-Length")
                        return

                    if length > 10 * 1024 * 1024:
                        self.send_error(413, "Request body too large")
                        return

                    body = self.rfile.read(length)
                    request = Order(
                        urlsplit(self.path).path,
                        dict(self.headers.items()),
                        body,
                        self.command,
                    )

                    print(
                        f"[{app.name}] {request.method} "
                        f'"{request.path}"'
                    )

                    response = app.make(request)

                    if isinstance(response.body, bytes):
                        response_body = response.body
                    elif isinstance(response.body, str):
                        response_body = response.body.encode("utf-8")
                    else:
                        response_body = json.dumps(response.body).encode("utf-8")

                    self.send_response(response.status_code)

                    for name, value in response.headers.items():
                        self.send_header(name, value)

                    if not any(
                        name.lower() == "content-length"
                        for name in response.headers
                    ):
                        self.send_header(
                            "Content-Length",
                            str(len(response_body)),
                        )

                    self.end_headers()
                    self.wfile.write(response_body)

                do_GET = _handle
                do_POST = _handle
                do_PUT = _handle
                do_PATCH = _handle
                do_DELETE = _handle

            server = ThreadingHTTPServer((host, port), Handler)
            print(f"[{self.name}] Running at http://{host}:{port}")
            server.serve_forever()
        except KeyboardInterrupt:
            print(f"\n[{self.name}] Server stopped.")

