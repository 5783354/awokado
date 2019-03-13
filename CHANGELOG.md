# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

## [Unreleased]

- implementation of JSONAPI.org format

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
