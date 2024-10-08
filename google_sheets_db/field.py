from typing import Any


class Field:

    def __init__(
            self,
            field_type: type = str,
            name: str = None,
            order_number: int = None,
            primary_key: bool = False,
            default: Any = '%#not_specified#%'
    ):
        self.name = name
        self.order_number = order_number
        self.primary_key = primary_key
        self.field_type = field_type
        self.default = field_type() if default == '%#not_specified#%' else default

    def __repr__(self):
        return f'Field({self.name})'

    def __get__(self, instance, owner):
        """Descriptor for retrieving a value from a field in a document."""
        if instance is None:
            # Document class being used rather than a document object
            return self

        # Get value from document instance if available
        value = instance._data.get(self.name) # noqa
        return value

    def __set__(self, instance, value):
        """Descriptor for assigning a value to a field in a document."""
        # If setting to None and there is a default value provided for this
        # field, then set the value to the default value.
        if value is None and self.default is not None:
            value = self.default
            if callable(value):
                value = value() # noqa

        instance._data[self.name] = value # noqa


class PrimaryKey(Field):

    def __init__(self, *args, field_type=None, default='%#not_specified#%', **kwargs):
        # Yes, it is a primary key, ignore the keyword
        kwargs.pop('primary_key', None)
        # By default: int
        if not field_type:
            field_type = int
            # Use 0 as default value for int may be misleading, let's use None
            if default == '%#not_specified#%':
                default = None
        super().__init__(*args, primary_key=True, field_type=field_type, default=default, **kwargs)

    def __repr__(self):
        return f'PrimaryKey({self.name})'
