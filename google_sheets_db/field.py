
class Field:

    def __init__(self, name=None, order_number=None, field_type=str, primary_key=False):
        self.name = name
        self.order_number = order_number
        self.primary_key = primary_key
        self.field_type = field_type


class PrimaryKey(Field):

    def __init__(self, **kwargs):
        kwargs.pop('primary_key', None)
        super().__init__(primary_key=True, **kwargs)
