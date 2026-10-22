
from rock import Rock, View, Order, Dish, Redirect, Render


app = Rock("Rocks Test Server")


# -------------------- Views --------------------

class HomeView(View):
    def get(self):
        return Dish(
            200,
            {"Content-Type": "text/html; charset=utf-8"},
            """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Rocks Test Server</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        max-width: 750px;
                        margin: 50px auto;
                        padding: 20px;
                        background: #f5f5f5;
                    }
                    section {
                        background: white;
                        padding: 20px;
                        margin-bottom: 15px;
                        border-radius: 10px;
                    }
                    a, button {
                        display: inline-block;
                        margin: 5px;
                        padding: 10px 14px;
                        background: #222;
                        color: white;
                        text-decoration: none;
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                    }
                    input {
                        padding: 10px;
                        margin: 5px;
                    }
                </style>
            </head>
            <body>
                <h1>Rocks Test Server</h1>
                <p>Your Rocks application is running.</p>

                <section>
                    <h2>Routing</h2>
                    <a href="/about">Static route</a>
                    <a href="/users/42">Dynamic route</a>
                    <a href="/articles">Optional parameter</a>
                    <a href="/articles/rocks">Optional parameter with value</a>
                </section>

                <section>
                    <h2>Responses</h2>
                    <a href="/json">JSON response</a>
                    <a href="/redirect">Redirect</a>
                    <a href="/missing">404 test</a>
                    <a href="/error">500 test</a>
                </section>

                <section>
                    <h2>POST request</h2>
                    <form method="post" action="/submit">
                        <input name="message" placeholder="Type a message">
                        <button type="submit">Submit</button>
                    </form>
                </section>

                <section>
                    <h2>Templates</h2>
                    <a href="/template">Template test</a>
                </section>
            </body>
            </html>
            """,
        )


class AboutView(View):
    def get(self):
        return Dish(200, {}, "Static route works!")


class UserView(View):
    def get(self, user_id):
        return Dish(200, {}, f"Dynamic route works! User ID: {user_id}")


class ArticleView(View):
    def get(self, slug=None):
        return Dish(200, {}, f"Article slug: {slug}")


class JSONView(View):
    def get(self):
        return Dish(
            200,
            {"Content-Type": "application/json"},
            {"framework": "Rocks", "status": "working"},
        )


class SubmitView(View):
    def post(self):
        body = self.request.body

        if isinstance(body, bytes):
            body = body.decode("utf-8", errors="replace")

        return Dish(
            200,
            {"Content-Type": "text/plain; charset=utf-8"},
            f"POST request received!\nBody: {body}",
        )


class RedirectView(View):
    def get(self):
        return Redirect("/about")


class TemplateView(View):
    def get(self):
        return Render(
            "test.html",
            {"title": "Rocks Templates", "message": "Template rendering works!"},
            template_dir="templates",
        )


class ErrorView(View):
    def get(self):
        raise RuntimeError("Intentional test exception")


# -------------------- Routes --------------------

app.carve({
    "/": HomeView,
    "/about": AboutView,
    "/users/<user_id>": UserView,
    "/articles/[<slug>]": ArticleView,
    "/json": JSONView,
    "/submit": SubmitView,
    "/redirect": RedirectView,
    "/template": TemplateView,
    "/error": ErrorView,
})


if __name__ == "__main__":
    app.hunt(host="127.0.0.1", port=8000)
