#Features

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
* gt
* lt


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

