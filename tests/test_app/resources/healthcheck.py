import falcon

from awokado.consts import CREATE, READ
from tests.test_app.resources.base import Resource


class HealthCheckResource(Resource):
    class Meta:
        model = None
        name = "healthcheck"
        methods = (READ, CREATE)
        auth = None

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
