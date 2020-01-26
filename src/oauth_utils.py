import datetime
from functools import wraps

from flask import session, request, redirect, url_for

from constants import COOKIE_TARGET_URL

AUTHORIZED_ROLES = ["staff", "instructor", "grader", "lab assistant"]
ENDPOINT = "cal/cs61a/sp20"


def is_staff(remote):
    try:
        token = session.get("dev_token") or request.cookies.get("dev_token")
        if not token:
            return False
        ret = remote.get("user")
        for course in ret.data["data"]["participations"]:
            if course["role"] not in AUTHORIZED_ROLES:
                continue
            if course["course"]["offering"] != ENDPOINT:
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
            if not is_staff(app.remote):
                resp = redirect(url_for("login"))
                expire_date = datetime.datetime.now() + datetime.timedelta(minutes=15)
                resp.set_cookie(COOKIE_TARGET_URL, request.url, expires=expire_date)
                return resp
            return route(*args, **kwargs)

        return wrapped

    return decorator