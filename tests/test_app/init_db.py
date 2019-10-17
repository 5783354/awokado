from awokado.db import database
from .models import Model

database.recreate()
database.create_models(Model.metadata)
