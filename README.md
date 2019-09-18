[![pipeline status](https://gitlab.com/5783354/awokado/badges/master/pipeline.svg)](https://gitlab.com/5783354/awokado/commits/master)[![coverage report](https://gitlab.com/5783354/awokado/badges/master/coverage.svg)](https://gitlab.com/5783354/awokado/commits/master)[![Codacy Badge](https://api.codacy.com/project/badge/Grade/349840fc0f144baba98aa04ad19bc10a)](https://www.codacy.com/app/5783354/awokado?utm_source=gitlab.com&amp;utm_medium=referral&amp;utm_content=5783354/awokado&amp;utm_campaign=Badge_Grade)[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)[![PyPI - Downloads](https://img.shields.io/pypi/dm/awokado.svg?style=popout)](https://pypi.org/project/awokado/)[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)![PyPI](https://img.shields.io/pypi/v/awokado)


Fast and flexible low-level API framework based on [Falcon](https://github.com/falconry/falcon), [Marshmallow](https://github.com/marshmallow-code/marshmallow/) and [SQLAlchemy Core](https://docs.sqlalchemy.org/en/latest/core/)

API is close to OpenAPI 3.0 specification

**Currently is under active development**

 ![Awokado Diagram](https://raw.githubusercontent.com/5783354/awokado/master/awokado_diagram.png)

# Documentation

You can find in: [Documentation](https://awokado.readthedocs.io/en/latest/)

# Changelog

You can find in: [CHANGELOG.md](https://gitlab.com/5783354/awokado/blob/master/CHANGELOG.md)

# Installation

```sh
$ pipenv install awokado
```
or
```sh
$ pip install awokado
```

Awokado uses [dynaconf](https://github.com/rochacbruno/dynaconf/) for loading it settings

You can find all available variables in `settings.toml` file

# Contributing

### Tests

To run tests locally you should create `.secrets.toml` file in the project root directory:

```toml
[default]
    DATABASE_PASSWORD='your_db_password_here'
    DATABASE_HOST='localhost'
    DATABASE_USER='your_db_username_here'
    DATABASE_PORT=5432 #DB port
    DATABASE_DB='test'

```
or

```toml
[default]
    DATABASE_URL='your_full_db_url'

```
Do not use both ways at the same time, you will get error!

Install required packages:

`$ pipenv install --dev`

Then you can setup your database: 

`$ pipenv python -m tests.test_app.init_db`

And run tests:

`$ pipenv python -m unittest`


# Authors
Is being made with the help of
 
[Alex Sidorov](mailto:alex.n.sidorov@gmail.com)

[Ksenia Malyavskaya](mailto:ksenia.malyavskaya@upsilonit.com)

[Pavel Danilyuk](mailto:pavel.danilyuk@upsilonit.com)

[Andrew Osenenko](mailto:andrew.osenenko@upsilonit.com)
