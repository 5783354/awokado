import falcon

from awokado.consts import CREATE, READ
from awokado.meta import ResourceMeta
from awokado.resource import BaseResource


class HealthCheckResource(BaseResource):
    Meta = ResourceMeta(name="healthcheck", methods=(READ, CREATE))

    def on_get(
        self,
        req: falcon.request.Request,
        resp: falcon.response.Response,
        resource_id: int = None,
    ):
        resp.body = "OK"

    def on_post(
        self, req: falcon.request.Request, resp: falcon.response.Response
    ):
        raise Exception("Something Goes Wrong")
