from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from pathlib import Path
import urllib.parse
import json
import mimetypes

from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader("."))

class HttpHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)

        if pr_url.path == "/":
            self.send_html_file("index.html")

        elif pr_url.path == "/message":
            self.send_html_file("message.html")

        elif pr_url.path == "/read":
            self.show_messages()

        elif Path(pr_url.path[1:]).exists():
            self.send_static()

        else:
            self.send_html_file("error.html", 404)

    def do_POST(self):
        if self.path == "/message":
            content_length = int(self.headers["Content-Length"])
            raw_data = self.rfile.read(content_length)

            data_parse = urllib.parse.unquote_plus(raw_data.decode("utf-8"))

            params = urllib.parse.parse_qs(data_parse)
            
            username = params.get("username", [""])[0]
            message = params.get("message", [""])[0]

            data_dict = {
                "ім'я користувача": username,
                "повідомлення": message
            }

            self.save_data(data_dict)

            self.send_response(302)
            self.send_header("Location", "/")
            self.end_headers()

    def save_data(self, data):
        file_path = Path("storage/data.json")

        file_path.parent.mkdir(exist_ok=True)

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            content = {}

        content[str(datetime.now())] = data

        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(content, file, ensure_ascii=False, indent=4)

    def show_messages(self):
        file_path = Path("storage/data.json")

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                messages = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            messages = {}

        template = env.get_template("read.html")
        html = template.render(messages=messages)

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        with open(filename, "rb") as file:
            self.wfile.write(file.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        
        if mt[0]:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", "application/octet-stream")
            
        self.end_headers()
        with open("." + self.path, "rb") as file:
            self.wfile.write(file.read())


def run():
    server_address = ("", 3000)
    http = HTTPServer(server_address, HttpHandler)
    print("Сервер працює на порту 3000...")
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер зупинено.")
        http.server_close()


if __name__ == "__main__":
    run()