import urllib.parse

import requests
from flask import session, url_for, request, redirect, abort, jsonify
from flask_oauthlib.client import OAuth
from werkzeug import security

from IGNORE_secrets import OAUTH_SECRET
from constants import COOKIE_TARGET_URL

CONSUMER_KEY = "61a-shortlinks"

CONSUMER_KEY = "61a-web-repl"  # temp!


def create_oauth_client(app):
    oauth = OAuth(app)
    app.secret_key = OAUTH_SECRET

    remote = oauth.remote_app(
        "ok-server",  # Server Name
        consumer_key=CONSUMER_KEY,
        consumer_secret=OAUTH_SECRET,
        request_token_params={"scope": "all", "state": lambda: security.gen_salt(10)},
        base_url="https://okpy.org/api/v3/",
        request_token_url=None,
        access_token_method="POST",
        access_token_url="https://okpy.org/oauth/token",
        authorize_url="https://okpy.org/oauth/authorize",
    )

    def check_req(uri, headers, body):
        """ Add access_token to the URL Request. """
        if "access_token" not in uri and session.get("dev_token"):
            params = {"access_token": session.get("dev_token")[0]}
            url_parts = list(urllib.parse.urlparse(uri))
            query = dict(urllib.parse.parse_qsl(url_parts[4]))
            query.update(params)

            url_parts[4] = urllib.parse.urlencode(query)
            uri = urllib.parse.urlunparse(url_parts)
        return uri, headers, body

    remote.pre_request = check_req

    @app.route("/oauth/login")
    def login():
        response = remote.authorize(callback=url_for("authorized", _external=True))
        return response

    @app.route("/oauth/authorized")
    def authorized():
        resp = remote.authorized_response()
        if resp is None:
            return "Access denied: error=%s" % (request.args["error"])
        if isinstance(resp, dict) and "access_token" in resp:
            session["dev_token"] = (resp["access_token"], "")

        if COOKIE_TARGET_URL in request.cookies:
            resp = redirect(request.cookies[COOKIE_TARGET_URL])
            resp.delete_cookie(COOKIE_TARGET_URL)
            return resp

        return redirect("/")

    @app.route("/api/user", methods=["POST"])
    def client_method():
        if "dev_token" not in session:
            abort(401)
        token = session["dev_token"][0]
        r = requests.get("https://okpy.org/api/v3/user/?access_token={}".format(token))
        if not r.ok:
            abort(401)
        return jsonify(r.json())

    @remote.tokengetter
    def get_oauth_token():
        return session.get("dev_token")

    app.remote = remote
