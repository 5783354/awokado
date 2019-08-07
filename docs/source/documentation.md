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