# API Methods
CREATE = "create"
READ = "read"
UPDATE = "update"
BULK_UPDATE = "bulk_update"
BULK_CREATE = "bulk_create"
DELETE = "delete"

# Audit logger level
AUDIT_DEBUG = "DEBUG"
AUDIT_INFO = "INFO"
AUDIT_WARNING = "WARNING"

# Filtering Operators
OP_LTE = "lte"
OP_EQ = "eq"
OP_GTE = "gte"
OP_ILIKE = "ilike"
OP_IN = "in"
OP_EMPTY = "empty"
OP_CONTAINS = "contains"

DEFAULT_ACCESS_CONTROL_HEADERS = [
    [
        "Access-Control-Allow-Headers",
        "Content-Type, X-File-Size, X-File-Name, Authorization",
    ],
    ["Access-Control-Allow-Credentials", "true"],
    ["Access-Control-Allow-Methods", "POST, PATCH, GET, OPTIONS, DELETE"],
    ["Access-Control-Max-Age", "3600"],
]
