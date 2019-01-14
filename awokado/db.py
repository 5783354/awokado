import stairs
from dynaconf import settings

DATABASE_PASSWORD = settings.DATABASE_PASSWORD
DATABASE_HOST = settings.DATABASE_HOST
DATABASE_USER = settings.DATABASE_USER
DATABASE_PORT = settings.DATABASE_PORT
DATABASE_DB = settings.DATABASE_DB

DATABASE_URL = (
    f"postgresql://"
    f"{DATABASE_USER}:{DATABASE_PASSWORD}@"
    f"{DATABASE_HOST}:{DATABASE_PORT}/"
    f"{DATABASE_DB}"
)

stairs.configure(DATABASE_URL)
