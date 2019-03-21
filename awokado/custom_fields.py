from marshmallow import fields, validate, utils


class ToMany(fields.List):
    def __init__(self, *args, **kwarg):
        related_resource_name = kwarg.get("resource")
        description = f"IDs of related resource ({related_resource_name})."

        users_description = kwarg.pop("description", None)
        if users_description:
            description = f"{description} {users_description}"

        super().__init__(*args, description=description, **kwarg)


class ToOne(fields.Integer):
    def __init__(self, *args, **kwarg):
        related_resource_name = kwarg.get("resource")
        description = f"ID of related resource ({related_resource_name})"

        users_description = kwarg.pop("description", None)
        if users_description:
            description = f"{description} {users_description}"

        super().__init__(*args, description=description, **kwarg)


class Choice(fields.Str):
    def __init__(self, *args, **kwarg):
        allowed_values = kwarg.get("allowed_values")
        super().__init__(
            *args, validate=validate.OneOf(allowed_values), **kwarg
        )
