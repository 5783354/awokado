import os
from typing import Union

from jinja2 import Environment, FileSystemLoader

from awokado.filter_parser import OPERATORS_MAPPING


def get_readme(template_abs_path: Union[str, None]) -> Union[str, None]:
    if not template_abs_path:
        return ""
    env = Environment(
        loader=FileSystemLoader(os.path.dirname(template_abs_path)),
        autoescape=True,
    )
    template = env.get_template(os.path.basename(template_abs_path))
    description = template.render(
        filter_ops=enumerate(OPERATORS_MAPPING.keys(), start=1)
    )
    return description
