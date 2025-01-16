from jinja2 import Environment, FileSystemLoader
import json


def render_read_page():
    env = Environment(loader=FileSystemLoader("."))

    template = env.get_template("read_template.html")
    with open("storage/data.json", "r") as file:
        load_data = json.load(file)

    output = template.render(messages=load_data, )

    with open("./base_pages/read.html", "w", encoding='utf-8') as fh:
        fh.write(output)
