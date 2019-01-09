import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

DEBUG = bool(os.getenv("DEBUG", False))

###############################################################################
# HTTP headers
###############################################################################

ORIGIN_HOSTS = ("https://frontend-domain-name.here:port",)

ACCESS_CONTROL_HEADERS = [
    (
        "Access-Control-Allow-Headers",
        "Content-Type, X-File-Size, X-File-Name, Authorization",
    ),
    ("Access-Control-Allow-Credentials", "true"),
    ("Access-Control-Allow-Methods", "POST, PATCH, GET, OPTIONS, DELETE"),
    ("Access-Control-Max-Age", "3600"),
]

AUTH_BEARER_SECRET = (
    "your secret token here"
    "your secret token here"
    "your secret token here"
    "your secret token here"
)
###############################################################################
# DB Settings
###############################################################################

DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "postgres")
DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
DATABASE_USER = os.getenv("DATABASE_USER", "postgres")
DATABASE_PORT = os.getenv("DATABASE_PORT", 5432)
DATABASE_DB = os.getenv("DATABASE_DB", "melon_example_db")

###############################################################################
# AWS S3 Settings
###############################################################################
AWS_S3_DEBUG_PROFILING_ACCESS_KEY = ""
AWS_S3_DEBUG_PROFILING_SECRET_KEY = ""
AWS_S3_DEBUG_PROFILING_BUCKET_NAME = ""
UPLOAD_DEBUG_PROFILING_TO_S3 = False

###############################################################################
###############################################################################

try:
    from settings_local import *
except:
    pass

###############################################################################
# Actions

# Setup db URL
DATABASE_URL = "postgresql://{}:{}@{}:{}/{}".format(
    DATABASE_USER, DATABASE_PASSWORD, DATABASE_HOST, DATABASE_PORT, DATABASE_DB
)
print(DATABASE_URL)
import stairs

stairs.configure(DATABASE_URL)
