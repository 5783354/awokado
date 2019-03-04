[![pipeline status](https://gitlab.com/5783354/awokado/badges/master/pipeline.svg)](https://gitlab.com/5783354/awokado/commits/master)[![coverage report](https://gitlab.com/5783354/awokado/badges/master/coverage.svg)](https://gitlab.com/5783354/awokado/commits/master)[![Codacy Badge](https://api.codacy.com/project/badge/Grade/349840fc0f144baba98aa04ad19bc10a)](https://www.codacy.com/app/5783354/awokado?utm_source=gitlab.com&amp;utm_medium=referral&amp;utm_content=5783354/awokado&amp;utm_campaign=Badge_Grade)[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)[![PyPI - Downloads](https://img.shields.io/pypi/dm/awokado.svg?style=popout)](https://pypi.org/project/awokado/)

Fast and flexible low-level API framework based on [Falcon](https://github.com/falconry/falcon), [Marshmallow](https://github.com/marshmallow-code/marshmallow/) and [SQLAlchemy Core](https://docs.sqlalchemy.org/en/latest/core/)

API is close to OpenAPI 3.0 specification

**Currently is under active development**

 ![Awokado Diagram](https://raw.githubusercontent.com/5783354/awokado/master/awokado_diagram.png)

# Changelog

You can find in: [CHANGELOG.md](https://gitlab.com/5783354/awokado/blob/master/CHANGELOG.md)

# Installation

```sh
$ pip install awokado
```

Awokado uses [dynaconf](https://github.com/rochacbruno/dynaconf/) for loading it settings

You can find all available variables in `settings.toml` file

# Filtering

#### syntax
`resource_field_name`\[`operator`\]=`value`
#### available operators
* lte
* eq
* gte
* ilike
* in
* empty
* contains

#### examples
`/v1/user/?username[ilike]=Andy`
it’s equal to SQL statement: `SELECT * FROM users WHERE username ILIKE '%Andy%';`

`/v1/user/?id[in]=1,2,3,4`
it’s equal to SQL statement: `SELECT * FROM users WHERE id IN (1,2,3,4);`

# Sorting

#### syntax

sort=`resource_field_name`,`-another_resource_field_name`

use `-` for descending order
#### examples
`/v1/user/?sort=name,-record_created`

# Includes

#### syntax
include=`resource_relation_name`

#### examples

`/v1/author/?include=books`

`/v1/author/?include=books,stores`

# Limit \ Offset (pagination)

#### syntax

limit=`integer`&offset=`integer`

#### examples
`/v1/user/?limit=10&offset=10`

`/v1/user/?offset=10`

`/v1/user/?limit=2000`

# Documentation

Awokado allows to generate documentation for a project using swagger(3rd version).
To generate documentation you need to import generate_documentation function and call it with required parameters.
Description of your project can be taken from template, in that case you need to provide path to the template as argument in `template_absolute_path`

#### function parameters
* api - your falcon.API instance
* api_host - IP address for your host
* project_name - title for your documentation
* output_dir - path, where swagger doc will be added
* api_version  `default "1.0.0"` - string with number of version of you project
* template_absolute_path `default None` - absolute path to template with description of your project

#### examples
```
from awokado.documentation import generate_documentation
from dynaconf import settings
from api.routes import api

generate_documentation(
    api=api,
    api_host=settings.MY_HOST_FOR_DOCUMENTATION,
    api_version="2.0.0",
    project_name="API Documentation",
    template_absolute_path="Users/my_user/projects/my_project/template.tmpl",
    output_dir="my_project/documentation",
)
```


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
Install required packages:

`$ pip install -r requirements/requirements-dev.txt`

Then you can setup your database: 

`$ python -m tests.test_app.init_db`

And run tests:

`$ python -m unittest`


# Authors
Is being made with the help of
 
[Alex Sidorov](mailto:alex.n.sidorov@gmail.com)

[Ksenia Malyavskaya](mailto:ksenia.malyavskaya@upsilonit.com)

[Pavel Danilyuk](mailto:pavel.danilyuk@upsilonit.com)

[Andrew Osenenko](mailto:andrew.osenenko@upsilonit.com)
