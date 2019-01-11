from marshmallow import fields, validate, utils


class Relation(fields.Field):
    def _serialize(self, value, attr, obj):
        return value


class ToMany(fields.List):
    def __init__(self, *args, **kwarg):
        related_resource_name = kwarg.get("resource")
        description = f"IDs of related resource ({related_resource_name})"

        super().__init__(*args, description=description, **kwarg)


class ToOne(fields.Integer):
    def __init__(self, *args, **kwarg):
        related_resource_name = kwarg.get("resource")
        description = f"ID of related resource ({related_resource_name})"

        super().__init__(*args, description=description, **kwarg)


class Choice(fields.Str):
    def __init__(self, *args, **kwarg):
        allowed_values = kwarg.get("allowed_values")
        super().__init__(
            *args, validate=validate.OneOf(allowed_values), **kwarg
        )


class NotNullableList(fields.List):
    def _serialize(self, value, attr, obj):
        if value is None:
            return []
        if utils.is_collection(value):
            return [
                self.container._serialize(each, attr, obj)
                for each in value
                if each is not None
            ]
        return [self.container._serialize(value, attr, obj)]
