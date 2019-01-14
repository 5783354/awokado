from awokado.resource import BaseResource


class Resource(BaseResource):
    class Meta:
        name = "_resource"
        methods = tuple()
        auth = None
        skip_doc = True

    def auth(self, *args, **kwargs):
        return None, None

    def audit_log(self, *args, **kwargs):
        return
