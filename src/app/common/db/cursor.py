from contextlib import contextmanager
from flask import g
import MySQLdb
from MySQLdb.cursors import DictCursor

from src.app.common.db.db import connection_params

@contextmanager
def get_cursor():
    """
    Returns a MySQL cursor.
    If something goes wrong, it will automatically roll back any changes.
    """
    if 'db' not in g:
        g.db = MySQLdb.connect(**connection_params)

    cursor = g.db.cursor(DictCursor)

    try:
        yield cursor
    except Exception:
        g.db.rollback()
        raise
    finally:
        cursor.close()
