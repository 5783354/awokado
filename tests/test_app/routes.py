import falcon

from awokado.middleware import HttpMiddleware
from awokado.utils import api_exception_handler
from .resources.author import AuthorResource
from .resources.book import BookResource
from .resources.store import StoreResource

api = falcon.API(middleware=[HttpMiddleware()])

###############################################################################
# Add API routes here #########################################################
###############################################################################
api.add_route("/v1/author/", AuthorResource())
api.add_route("/v1/author/{resource_id}", AuthorResource())
api.add_route("/v1/book/", BookResource())
api.add_route("/v1/book/{resource_id}", BookResource())
api.add_route("/v1/store/", StoreResource())
api.add_route("/v1/store/{resource_id}", StoreResource())

###############################################################################
###############################################################################
api.add_error_handler(Exception, api_exception_handler)
