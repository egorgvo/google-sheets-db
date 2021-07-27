
class Field:

    def __init__(self, field_type=str, name=None, order_number=None, primary_key=False):
        self.name = name
        self.order_number = order_number
        self.primary_key = primary_key
        self.field_type = field_type


class PrimaryKey(Field):

    def __init__(self, *args, **kwargs):
        kwargs.pop('primary_key', None)
        super().__init__(*args, primary_key=True, **kwargs)
