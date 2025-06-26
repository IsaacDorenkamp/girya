import sqlite3


def db_connection():
    raise ValueError()
    connection = sqlite3.connect("")
    try:
        yield connection
    finally:
        connection.close()
