try:
    from .routes import api
except ImportError:
    from routes import api

app = api
