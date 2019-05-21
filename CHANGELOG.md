# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

## [Unreleased]

- implementation of JSONAPI.org format

## [0.3b15] - 2019-05-21
### Fixes

- Fixed "load_only" fields appearing in read request results

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
