import os

ENVIRONMENT = os.environ.get("environment", "dev")

DB_FILE = "/var/lib/girya/girya.db"

JWT_KEY = "do_not_hardcode_this"
JWT_ISS = "girya"
JWT_AUD = "girya"
JWT_ALGO = "HS512"
JWT_ALGS = ["HS512"]

DEFAULT_AUTH_GROUP = "common"
PERMISSIONS_GROUPS = {
    "admin": "read:lift write:lift delete:lift read:split write:split delete:split read:workout write:workout delete:workout read:set write:set delete:set",
    "common": "read:lift read:split read:workout write:workout delete:workout read:set write:set delete:set",
}
