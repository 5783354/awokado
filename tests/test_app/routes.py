import falcon

from awokado.middleware import HttpMiddleware
from awokado.settings import DATABASE_URL
from .resources.author import AuthorResource
from .resources.book import BookResource

assert DATABASE_URL
api = falcon.API(middleware=[HttpMiddleware()])

###############################################################################
# Add API routes here #########################################################
###############################################################################
api.add_route("/v1/author/", AuthorResource())
api.add_route("/v1/author/{resource_id}", AuthorResource())
api.add_route("/v1/book/", BookResource())
api.add_route("/v1/book/{resource_id}", BookResource())
