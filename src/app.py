from flask import Flask, redirect, request
import requests

import urllib.parse as urlparse

from IGNORE_secrets import AUTH_SECRET
from oauth import create_oauth_client
from oauth_utils import secure


def add_url_params(url, params_string):
    parse_result = list(urlparse.urlsplit(url))
    parse_result[3] = "&".join(filter(lambda s: s, [parse_result[3], params_string]))
    return urlparse.urlunsplit(tuple(parse_result))


app = Flask(__name__)
if __name__ == '__main__':
    app.debug = True
create_oauth_client(app)

links, author = {}, {}

AUTH_CLIENT_NAME = "secure-internal-links"
DOC_URL = "https://docs.google.com/spreadsheets/d/1wxixgeehUtpXf1TQaFUiSSi_cOA-Tlz8c6o8fTodG_c/edit#gid=0"
SHEETS = ["Sheet1"]


@app.route("/<path>/")
@secure(app)
def handler(path):
    if not links:
        refresh()
    if path in links and links[path]:
        return redirect(
            add_url_params(links[path], request.query_string.decode("utf-8"))
        )
    return to_links(path)


@app.route("/preview/<path>/")
@secure(app)
def preview(path):
    if not links:
        refresh()
    if path not in links:
        return "No such link exists."
    return 'Points to <a href="{0}">{0}</a> by {1}'.format(
        add_url_params(links[path], request.query_string.decode("utf-8")), author[path]
    )


@app.route("/")
def base():
    return redirect("https://cs61a.org")


def to_links(path):
    return redirect("https://links.cs61a.org/" + path)


@app.route("/_refresh/")
@secure(app)
def refresh():
    links.clear()
    author.clear()
    for sheet_name in SHEETS:
        csvr = requests.post("https://auth.apps.cs61a.org/google/read_spreadsheet", json={
            "url": DOC_URL,
            "sheet_name": sheet_name,
            "client_name": AUTH_CLIENT_NAME,
            "secret": AUTH_SECRET,
        }).json()
        headers = [x.lower() for x in csvr[0]]
        for row in csvr[1:]:
            row = row + [""] * 5
            shortlink = row[headers.index("shortlink")]
            url = row[headers.index("url")]
            creator = row[headers.index("creator")]
            links[shortlink] = url
            author[shortlink] = creator
    return "Links updated"


if __name__ == "__main__":
    app.run()
