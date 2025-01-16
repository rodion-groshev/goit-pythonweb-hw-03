from http.server import HTTPServer, BaseHTTPRequestHandler
from pymongo.server_api import ServerApi
from template import render_read_page
from multiprocessing import Process
from pymongo import MongoClient
import urllib.parse
import mimetypes
import datetime
import pathlib
import socket
import json


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('./base_pages/index.html')
        elif pr_url.path == '/message.html':
            self.send_html_file('./base_pages/message.html')
        elif pr_url.path == '/read.html':
            render_read_page()
            self.send_html_file('./base_pages/read.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('./base_pages/error.html', 404)

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(data, ("localhost", 5000))
        self.send_response(302)
        self.send_header('Location', '/message.html')
        self.end_headers()
        sock.close()

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())


def run_http(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ('', 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


def run_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("localhost", 5000))
    try:
        while True:
            data, address = sock.recvfrom(1024)
            print(f'Received data: {data.decode()} from: {address}')
            data_parse = urllib.parse.unquote_plus(data.decode())
            data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
            save_local(data_dict)
    except KeyboardInterrupt:
        print(f'Destroy server')
    finally:
        sock.close()


def save_local(data):
    with open("storage/data.json", "r") as read_file:
        load_data = json.load(read_file)

    time_now = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S.%f')
    load_data[time_now] = data

    with open("storage/data.json", "w") as write_file:
        json.dump(load_data, write_file)

    save_mangodb(load_data)


def save_mangodb(data):
    client = MongoClient(
        "mongodb+srv://rodiongroshev:uK5UdDyi615a1jll@clusteredu.obrwfus.mongodb.net/?retryWrites=true&w=majority&appName"
        "=ClusterEdu",
        server_api=ServerApi('1')
    )
    db = client.book

    try:
        db.hw.insert_one(data)
    except:
        print("Something went wrong")


if __name__ == '__main__':
    http_server = Process(target=run_http)
    socket_server = Process(target=run_socket)

    http_server.start()
    socket_server.start()
    http_server.join()
    socket_server.join()
