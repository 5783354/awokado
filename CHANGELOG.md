# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
## [0.5b2] - 2019-10-28

### Fixes

- Move args parsing to FilterItem dataclass
- Fix typing issues
- Fix code duplication in validate_create_request

## [0.5b1] - 2019-10-28

### Fixes

- Fix bug in ReadContext imports

## [0.5b0] - 2019-10-25

### Changed

- Argument `resp: falcon.Response` removed from functions `validate_create_request` and `validate_update_request`
- Read logic moved to `ReadContext` class

## [0.4b5] - 2019-10-16

### Added

- Class for database config

### Changed

- Move cached_property to deps
- Now we use Python 3.7

## [0.4b4] - 2019-10-15

### Fixes

- Fix receiving field from relative model

## [0.4b3] - 2019-09-24

### Fixes

- `Resource.Meta.skip_doc = True` was generating broken swagger.yml 

## [0.4b2] - 2019-09-23

### Added

- Added lt and gt operators in filtering.

## [0.4b1] - 2019-09-18

### Added

- [pipenv](https://docs.pipenv.org) implemented.
- [mypy](http://mypy-lang.org) implemented.
- `awokado.response.Response` class added. [Read more](https://awokado.readthedocs.io/en/latest/reference.html#awokado.response.Response)
- method `awokado.resource.BaseResource.read__serializing` now uses `awokado.response.Response` class to serialize data. Take a look at the [code](https://gitlab.com/5783354/awokado/blob/master/awokado/resource.py#L655) if you already override this method

### Changed

- `awokado.utils.ReadContext` moved to `awokado.request.ReadContext`

### Removed

- `awokado.utils.empty_response` function removed (use `awokado.response.Response` instead)

## [0.3b19] - 2019-08-28

### Added

- Added documentation.


## [0.3b17] - 2019-07-18

### Added

- Added ability to use any resource field as "id" field. Currently only for read logic. This field can be specified as `id_field` attribute of resource's `Meta` class
- Added schema validation for POST requests with a friendly message about the exception

## [0.3b16] - 2019-05-24

### Changed

Updated falcon from 1.4.1 to 2.0.0 ([Falcon 2 Changelog](https://falcon.readthedocs.io/en/latest/changes/2.0.0.html)), which led to following changes:
- `application.req_options.auto_parse_qs_csv` param is now `False` by default, so you'll need to manually set it to `True`
- `application.req_options.strip_url_path_trailing_slash ` param is now `False` by default, so you'll need to manually set it to `True`
- For direct data read from request `req.bounded_stream` is now used instread of `req.stream`.

## [0.3b15] - 2019-05-23

### Added

- Added pre-commit hook to run black formatting checks
- Added ability to specify full database url in settings

### Fixes

- Fixed "load_only" fields appearing in read request results
- Fixed “awokado_debug” setting being always required in settings
- Fixed attribute “auth” being mandatory in resource.Meta
- Fixed method “auth” being mandatory to overwrite in resource
- Fixed method “audit_log” being mandatory to overwrite in resource

### Removed
    
- Functions `set_bearer_header`, `get_bearer_payload` and `AWOKADO_AUTH_BEARER_SECRET` var are removed 

## [0.3b14] - 2019-05-15
### Fixes

- Fixed documentation generation for bulk operations


## [0.3b13] - 2019-04-02
### Changed

No backward compatibility. Need to change custom delete() and can_create() methods.
- `delete` method supports bulk delete. 
- add `payload` attribute to `can_create` method.

## [0.3b12] - 2019-03-14
### Added
- `select_from` attribute in class Meta, allows you to specify `sqlalchemy.select_from()` arguments. Example: 

```python
class AuthorResource(Resource):
    class Meta:
        model = m.Author
        name = "author"
        methods = (CREATE, READ, UPDATE, BULK_UPDATE, DELETE)
        auth = None
        select_from = sa.outerjoin(
            m.Author, m.Book, m.Author.id == m.Book.author_id
        )
``` 

### Deprecated
- `join` argument in the resource field 

## [0.3b11] - 2019-03-13
### Added

- ability to make list of joins in resource field 
    
    ```python 
        book_titles = fields.List(
        fields.Str(),
        resource="author",
        model_field=sa.func.array_remove(sa.func.array_agg(m.Book.title), None),
        join=[
            OuterJoin(
                m.Tag, m.M2M_Book_Tag, m.Tag.id == m.M2M_Book_Tag.c.tag_id
            ),
            OuterJoin(
                m.M2M_Book_Tag, m.Book, m.M2M_Book_Tag.c.book_id == m.Book.id
            ),
        ],
    )
    ```


## [0.3b10] - 2019-03-11
### Added

- Automated SQL generation for `POST/PATCH` requests


## [0.3b7] - 2019-03-05
### Added

- `bulk_create` method in base resource

### Deprecated

- `create` method (is going to be replaced with bulk_create)

## [0.3b5] - 2019-03-04
### Added

- API simple workflow diagram
- `disable_total` attr for Resource.Meta. Set it to `True` to avoid adding total column: `sa.func.count().over()`. Useful for `historical` tables, where pagination based on date instead of limit / offset to not overload SQL database

### Fixes

- Fixed `description` arg for `ToMany` and `ToOne` fields (was broken)

## [0.3b2] - 2019-03-01
### Added

- Documentation generation for API resources
- Automated SQL generation for `GET` requests (including ToOne and ToMany relation fields)
- AWOKADO_DEBUG handle traceback exception in API response

### Changed

- all `Forbidden` exceptions now raise HTTP_403 instead of HTTP_401

### Deprecated

-

### Removed

- 

### Fixed

- 
