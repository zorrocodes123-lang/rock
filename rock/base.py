from typing import Any, Callable
from http.server import BaseHTTPRequestHandler, HTTPServer
from .request  import *
from .response import *
from .views import *
from .routing import *

class Rock:
    '''Base class for the application.'''
    def __init__(self, name: str = "Rock"):
        '''Initialize the application with a name'''
        assert isinstance(name, str), "Name should be a string."
        self.name: str = name
        self.routes: dict[str, type[View]] = {}
        self.dynamic_routes = []

    def carve(self, routes: dict[str, type[View]]) -> None:
        assert isinstance(routes, dict), "Routes must be a dictionary."

        for path, view in routes.items():
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
                    length = int(self.headers.get("Content-Length", 0))
                    body = self.rfile.read(length)

                    request = Order(
                        self.path,
                        self.headers,
                        body,
                        self.command,
                    )

                    print(
                        f"[{app.name}] {request.method} "
                        f'"{request.path}"'
                    )

                    response = app.make(request)

                    response_body = (
                        response.body
                        if isinstance(response.body, bytes)
                        else str(response.body).encode("utf-8")
                    )

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

            server = HTTPServer((host, port), Handler)
            print(f"[{self.name}] Running at http://{host}:{port}")
            server.serve_forever()
        except KeyboardInterrupt as k:
            import sys
            sys.exit(1)
        except Exception as e:
            print(e)

