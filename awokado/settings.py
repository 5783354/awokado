import os

from dynaconf import settings

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
AWOKADO_DEBUG = settings.get("AWOKADO_DEBUG", False)
###############################################################################
# HTTP headers
###############################################################################

AWOKADO_ORIGIN_HOSTS = settings.get(
    "AWOKADO_ORIGIN_HOSTS", "https://frontend-domain-name.here:port"
)
ACCESS_CONTROL_HEADERS = [
    (
        "Access-Control-Allow-Headers",
        "Content-Type, X-File-Size, X-File-Name, Authorization",
    ),
    ("Access-Control-Allow-Credentials", "true"),
    ("Access-Control-Allow-Methods", "POST, PATCH, GET, OPTIONS, DELETE"),
    ("Access-Control-Max-Age", "3600"),
]

AWOKADO_AUTH_BEARER_SECRET = settings.get(
    "AWOKADO_AUTH_BEARER_SECRET", "YourSecretTokenHere"
)
###############################################################################
# DB Settings
###############################################################################
DATABASE_PASSWORD = settings.get("DATABASE_PASSWORD", "postgres")
DATABASE_HOST = settings.get("DATABASE_HOST", "postgres")
DATABASE_USER = settings.get("DATABASE_USER", "postgres")
DATABASE_PORT = settings.get("DATABASE_PORT", 5432)
DATABASE_DB = settings.get("DATABASE_DB", "test")

###############################################################################
# AWS S3 Settings
###############################################################################
AWOKADO_AWS_S3_DEBUG_PROFILING_ACCESS_KEY = settings.get(
    "AWOKADO_AWS_S3_DEBUG_PROFILING_ACCESS_KEY", ""
)
AWOKADO_AWS_S3_DEBUG_PROFILING_SECRET_KEY = settings.get(
    "AWOKADO_AWS_S3_DEBUG_PROFILING_ACCESS_KEY", ""
)
AWOKADO_AWS_S3_DEBUG_PROFILING_BUCKET_NAME = settings.get(
    "AWOKADO_AWS_S3_DEBUG_PROFILING_ACCESS_KEY", ""
)
AWOKADO_ENABLE_UPLOAD_DEBUG_PROFILING_TO_S3 = settings.get(
    "AWOKADO_AWS_S3_DEBUG_PROFILING_ACCESS_KEY", False
)

###############################################################################
# Actions

# Setup db URL
DATABASE_URL = (
    f"postgresql://"
    f"{DATABASE_USER}:{DATABASE_PASSWORD}@"
    f"{DATABASE_HOST}:{DATABASE_PORT}/"
    f"{DATABASE_DB}"
)

import stairs

stairs.configure(DATABASE_URL)
