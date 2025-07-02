DB_FILE = "/var/misc/girya.db"

JWT_KEY = "do_not_hardcode_this"
JWT_ISS = "girya"
JWT_AUD = "girya"
JWT_ALGO = "HS512"
JWT_ALGS = ["HS512"]

PERMISSIONS_GROUPS = {
    "admin": "read:lift write:lift read:split write:split read:workout write:workout delete:workout",
    "common": "read:lift read:split read:workout write:workout delete:workout",
}
