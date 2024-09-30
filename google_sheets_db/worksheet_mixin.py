from typing import Any

from gspread.models import Spreadsheet, Worksheet


def check_spreadsheet(func):
    def decorator(self, *args, **kwargs):
        if not hasattr(self, '_db') or not self._db:
            raise Exception("No spreadsheet defined.")
        return func(self, *args, **kwargs)
    return decorator


def check_sheet(func):
    def decorator(self, *args, **kwargs):
        if not hasattr(self, '_sheet') or not self._sheet:
            raise Exception("No sheet defined.")
        return func(self, *args, **kwargs)
    return decorator


class WorksheetMixin:
    _db: Spreadsheet
    _sheet: Worksheet

    @classmethod
    @check_sheet
    def get_all_values(cls) -> list[list[Any]]:
        """Returns all shet values"""
        return cls._sheet.get_all_values()

    @classmethod
    @check_sheet
    def get_column_values(cls, order_number: int) -> list[Any]:
        return cls._sheet.col_values(order_number)

    @classmethod
    @check_sheet
    def truncate(cls):
        return cls._sheet.clear()
