import sqlite3


def main(argv: list[str]):
    import config

    connection = sqlite3.connect(config.DB_FILE)
    email = argv[1]

    cursor = connection.execute("UPDATE user SET auth_group=\"admin\" WHERE email=?", (email,))
    connection.commit()
    if cursor.rowcount == 0:
        print(f"Could not find user '{email}'")
    else:
        print(f"Made '{email}' an admin")


if __name__ == '__main__':
    import sys
    import os

    parent = os.path.dirname(os.path.dirname(__file__))
    sys.path.append(os.path.join(parent, "src"))

    main(sys.argv)

