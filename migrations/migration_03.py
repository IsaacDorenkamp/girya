import sqlite3


def migrate(connection: sqlite3.Connection):
    connection.executescript("""
BEGIN;
CREATE TABLE lift_set2(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lift_slug VARCHAR NOT NULL REFERENCES lift(slug) ON DELETE CASCADE,
    workout_slug VARCHAR NOT NULL REFERENCES workout(slug) ON DELETE CASCADE,
    reps INTEGER NOT NULL,
    weight REAL NOT NULL,
    weight_unit VARCHAR NOT NULL
);
INSERT INTO lift_set2 (id, lift_slug, workout_slug, reps, weight, weight_unit)
SELECT id, lift_slug, workout_slug, reps, weight, weight_unit FROM lift_set;
DROP TABLE lift_set;
ALTER TABLE lift_set2 RENAME TO lift_set;
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
