# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

## [Unreleased]

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
