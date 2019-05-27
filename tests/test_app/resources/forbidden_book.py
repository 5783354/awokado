from marshmallow import fields

import tests.test_app.models as m
from awokado.auth import BaseAuth
from awokado.consts import CREATE, READ, UPDATE, BULK_UPDATE, DELETE
from tests.test_app.resources.base import Resource


class ForbiddenBookResource(Resource):
    class Meta:
        model = m.Book
        name = "forbidden_book"
        methods = (CREATE, READ, UPDATE, BULK_UPDATE, DELETE)
        auth = BaseAuth

    id = fields.Int(model_field=m.Book.id)
    title = fields.String(model_field=m.Book.title, required=True)
    description = fields.String(model_field=m.Book.description)
