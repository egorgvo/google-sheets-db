from gspread.models import Worksheet


def check_sheet(func):
    def decorator(self, *args, **kwargs):
        if not self._sheet:
            raise Exception("No sheet defined.")
        return func(self, *args, **kwargs)

    return decorator


class WorksheetMixin():
    _sheet: Worksheet = None

    @classmethod
    @check_sheet
    def get_all_values(cls):
        return cls._sheet.get_all_values()

    @classmethod
    @check_sheet
    def get_column_values(cls, order_number):
        return cls._sheet.col_values(order_number)
