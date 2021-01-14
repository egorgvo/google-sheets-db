COLUMN_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


class Field:

    def __init__(self, name, order_number, field_type=str):
        self.name = name
        self.order_number = order_number
        self.field_type = field_type
        self.char = COLUMN_CHARS[self.order_number]
