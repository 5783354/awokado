[![pipeline status](https://gitlab.com/5783354/awokado/badges/master/pipeline.svg)](https://gitlab.com/5783354/awokado/commits/master)
[![coverage report](https://gitlab.com/5783354/awokado/badges/master/coverage.svg)](https://gitlab.com/5783354/awokado/commits/master)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/349840fc0f144baba98aa04ad19bc10a)](https://www.codacy.com/app/5783354/awokado?utm_source=gitlab.com&amp;utm_medium=referral&amp;utm_content=5783354/awokado&amp;utm_campaign=Badge_Grade)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

Fast and flexible low-level API framework based on Falcon and SQLAlchemy Core

API is close to OpenAPI 3.0 specification

**Currently is under active development**

# Setup

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

# sorting
#### syntax

sort=`resource_field_name`,`-another_resource_field_name`

use `-` for descending order
#### examples
`/v1/user/?sort=name,-record_created`

# includes

#### syntax
include=`resource_relation_name`

#### examples

`/v1/author/?include=books`

`/v1/author/?include=books,stores`

#limit \ offset
#### syntax

limit=`integer`&offset=`integer`

#### examples
`/v1/user/?limit=10&offset=10`

`/v1/user/?offset=10`

`/v1/user/?limit=2000`

# Authors
Is being made with the help of
 
[Alex Sidorov](mailto:alex.n.sidorov@gmail.com)

[Ksenia Malyavskaya](mailto:ksenia.malyavskaya@upsilonit.com)

[Pavel Danilyuk](mailto:pavel.danilyuk@upsilonit.com)

[Andrew Osenenko](mailto:andrew.osenenko@upsilonit.com)
