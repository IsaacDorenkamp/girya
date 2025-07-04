import sqlite3


def migrate(connection: sqlite3.Connection):
    connection.executescript("""
BEGIN;
CREATE TABLE user(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR UNIQUE NOT NULL,
    auth_group VARCHAR NOT NULL,
    first_name VARCHAR NOT NULL,
    last_name VARCHAR NOT NULL,
    password VARCHAR NOT NULL
);
CREATE TABLE lift(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR NOT NULL,
    slug VARCHAR UNIQUE NOT NULL
);
CREATE TABLE split(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR NOT NULL,
    slug VARCHAR UNIQUE NOT NULL
);
CREATE TABLE split_lift(
    split_id INTEGER NOT NULL,
    lift_id INTEGER NOT NULL,
    PRIMARY KEY (split_id, lift_id),
    FOREIGN KEY (split_id) REFERENCES split(id),
    FOREIGN KEY (lift_id) REFERENCES lift(id),
    UNIQUE(split_id, lift_id) ON CONFLICT ROLLBACK
);
CREATE TABLE workout(
    at DATETIME NOT NULL,
    slug VARCHAR PRIMARY KEY,
    split_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (split_id) REFERENCES split(id),
    FOREIGN KEY (user_id) REFERENCES user(id)
);
CREATE TABLE lift_set(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lift_slug VARCHAR NOT NULL,
    workout_slug VARCHAR NOT NULL,
    reps INTEGER NOT NULL,
    weight REAL NOT NULL,
    weight_unit VARCHAR NOT NULL,
    FOREIGN KEY (lift_slug) REFERENCES lift(slug),
    FOREIGN KEY (workout_slug) REFERENCES workout(slug)
);
COMMIT;
""")


if __name__ == '__main__':
    import sys
    import os

    parent = os.path.dirname(os.path.dirname(__file__))
    sys.path.append(os.path.join(parent, "src"))

    import config

    connection = sqlite3.connect(config.DB_FILE)
    migrate(connection)
