from flask import render_template


def render_error(message: str, status_code: int):
    return render_template("error.html", message=message), status_code
