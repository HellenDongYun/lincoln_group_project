from flask import request
from markupsafe import Markup


def nav_link(url, label):
    """
    Returns an <a> tag with classes and aria-current for the active link.
    """
    is_active = request.path == url
    classes = "nav-link active" if is_active else "nav-link"
    aria_current = 'aria-current="page"' if is_active else ""

    return Markup(f'<a class="{classes}" href="{url}" {aria_current}>{label}</a>')
#  how to use in jinja template : {{ nav_link('/', 'Home') }} <!-- output: <a href="/" class="nav-link">Home</a> -->