from awokado.settings import DATABASE_URL
from .routes import api

assert DATABASE_URL
app = api
