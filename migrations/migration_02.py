import sqlite3


def migrate(connection: sqlite3.Connection):
    connection.executescript("""
BEGIN;
CREATE TABLE split_lift2(
    split_id INTEGER NOT NULL,
    lift_id INTEGER NOT NULL,
    PRIMARY KEY (split_id, lift_id),
    FOREIGN KEY (split_id) REFERENCES split(id) ON DELETE CASCADE,
    FOREIGN KEY (lift_id) REFERENCES lift(id) ON DELETE CASCADE,
    UNIQUE(split_id, lift_id) ON CONFLICT ROLLBACK
);
INSERT INTO split_lift2 (split_id, lift_id)
SELECT split_id, lift_id FROM split_lift;
DROP TABLE split_lift;
ALTER TABLE split_lift2 RENAME TO split_lift;
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
