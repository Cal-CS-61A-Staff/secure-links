import datetime
from functools import wraps
from urllib.parse import urlparse

import requests
from cachetools import TTLCache
from flask import session, request, redirect, url_for

from constants import COOKIE_TARGET_URL

AUTHORIZED_ROLES = ["staff", "instructor", "grader"]
COURSE = "cs61a"

_cache = TTLCache(100, 60 * 30)


def get_endpoint():
    if "cs61a" not in _cache:
        _cache["cs61a"] = requests.post(f"https://auth.apps.cs61a.org/api/{COURSE}/get_endpoint").json()
    return _cache["cs61a"]


def is_staff(remote):
    try:
        token = session.get("dev_token") or request.cookies.get("dev_token")
        if not token:
            return False
        ret = remote.get("user")
        for course in ret.data["data"]["participations"]:
            if course["role"] not in AUTHORIZED_ROLES:
                continue
            if course["course"]["offering"] != get_endpoint():
                continue
            return True
        return False
    except Exception as e:
        # fail safe!
        print(e)
        return False


def secure(app):
    def decorator(route):
        @wraps(route)
        def wrapped(*args, **kwargs):
            url = urlparse(request.url)
            if url.netloc == "go":
                redirect_url = url._replace(netloc="go.cs61a.org")
                return redirect(redirect_url.geturl())
            if not is_staff(app.remote):
                resp = redirect(url_for("login"))
                expire_date = datetime.datetime.now() + datetime.timedelta(minutes=15)
                resp.set_cookie(COOKIE_TARGET_URL, request.url, expires=expire_date)
                return resp
            return route(*args, **kwargs)

        return wrapped

    return decorator
