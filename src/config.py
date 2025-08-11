import os

from definitions import Environment


ENVIRONMENT = Environment(os.environ.get("environment", "dev"))

if ENVIRONMENT == Environment.dev:
    CORS_ORIGINS = ["http://localhost:5173"]
else:
    CORS_ORIGINS = []


DB_FILE = "/var/lib/girya/girya.db"

JWT_KEY = os.environ["GIRYA_JWT_KEY"]
JWT_ISS = "girya"
JWT_AUD = "girya"
JWT_ALGO = "HS512"
JWT_ALGS = ["HS512"]

DEFAULT_AUTH_GROUP = "common"
PERMISSIONS_GROUPS = {
    "admin": "read:lift write:lift delete:lift read:split write:split delete:split read:workout write:workout delete:workout read:set write:set delete:set",
    "common": "read:lift read:split read:workout write:workout delete:workout read:set write:set delete:set",
}
