from functools import wraps
from flask import redirect, url_for, session


def redirect_to_login():
    return redirect(url_for("login"))
        

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(session)
        if session.get("is_authenticated"):
            return func(*args, **kwargs)
        return redirect_to_login()
    return wrapper


def student_login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(session)
        if session.get("role") == "student":
            return func(*args, **kwargs)
        return redirect_to_login()
    return wrapper


def mentor_login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(session)
        if session.get("role") == "mentor":
            return func(*args, **kwargs)
        return redirect_to_login()
    return wrapper


def staff_login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(session)
        if session.get("role") == "staff":
            return func(*args, **kwargs)
        return redirect_to_login()
    return wrapper

# staff, mentor or student login required
def sms_login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(session)
        if session.get("role") == "staff" or session.get("role") == "mentor" or session.get("role") == "student":
            return func(*args, **kwargs)
        return redirect_to_login()
    return wrapper