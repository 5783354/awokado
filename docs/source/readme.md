# README

## Filtering

##### syntax
`resource_field_name`\[`operator`\]=`value`
##### available operators
* lte
* eq
* gte
* ilike
* in
* empty
* contains

##### examples
`/v1/user/?username[ilike]=Andy`
it’s equal to SQL statement: `SELECT * FROM users WHERE username ILIKE '%Andy%';`

`/v1/user/?id[in]=1,2,3,4`
it’s equal to SQL statement: `SELECT * FROM users WHERE id IN (1,2,3,4);`

## Sorting

##### syntax

sort=`resource_field_name`,`-another_resource_field_name`

use `-` for descending order
##### examples
`/v1/user/?sort=name,-record_created`

## Includes

##### syntax
include=`resource_relation_name`

##### examples

`/v1/author/?include=books`

`/v1/author/?include=books,stores`

## Limit \ Offset (pagination)

##### syntax

limit=`integer`&offset=`integer`

##### examples
`/v1/user/?limit=10&offset=10`

`/v1/user/?offset=10`

`/v1/user/?limit=2000`

## Documentation

Awokado allows to generate documentation for a project using swagger(3rd version).
To generate documentation you need to import generate_documentation function and call it with required parameters.
Description of your project can be taken from template, in that case you need to provide path to the template as argument in `template_absolute_path`

##### function parameters
* api - your falcon.API instance
* api_host - IP address for your host
* project_name - title for your documentation
* output_dir - path, where swagger doc will be added
* api_version  `default "1.0.0"` - string with number of version of you project
* template_absolute_path `default None` - absolute path to template with description of your project

##### examples
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