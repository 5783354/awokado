from awokado.resource import BaseResource


class Resource(BaseResource):
    class Meta:
        name = "_resource"
        methods = tuple()
        auth = None
        skip_doc = True
