import inspect
import types
from functools import lru_cache
from itertools import chain

from gspread.models import Spreadsheet, Worksheet

from google_sheets_db import Field, GoogleSheetsDB


class BaseSheetMetaclass(type):

    def __repr__(self):
        return self.__name__

    def __init__(self, name, bases, attrs):
        super().__init__(name, bases, attrs)
        self.__sheet = None

    @property
    @lru_cache
    def _db(cls) -> Spreadsheet:
        if cls.meta.get('spreadsheet_id'):
            spreadsheets = [s for s in GoogleSheetsDB.spreadsheets if s.spreadsheet_id == cls.meta['spreadsheet_id']]
            if not spreadsheets:
                raise Exception(f"Spreadsheet {cls.meta['spreadsheet_id']} is not declared.")
        elif GoogleSheetsDB.spreadsheets:
            spreadsheets = GoogleSheetsDB.spreadsheets
        else:
            raise Exception("No spreadsheet specified.")
        return spreadsheets[0]

    @property
    @lru_cache
    def _sheet_name(cls) -> str:
        return cls.meta.get('sheet_name') or cls.__name__

    @property
    def _sheet(cls) -> Worksheet:
        if cls.__sheet:
            return cls.__sheet

        cls.__sheet = cls._db.get_sheet_by_name(cls._sheet_name)
        return cls.__sheet

    def exists(self) -> bool:
        return self._db.sheet_exists(name=self._sheet_name)

    def create_sheet_if_not_exists(self) -> Worksheet:
        self.__sheet = self._db.create_sheet_if_not_exists(name=self._sheet_name)
        return self._sheet

    def drop(self):
        self._db.drop_sheet(self._sheet)
        self.__sheet = None

    @property
    @lru_cache
    def _columns(cls) -> list[Field]:
        attrs = dict(cls.__dict__.items())
        # Remove inner variables
        attrs.pop('meta', None)
        for name, value in list(attrs.items()):
            for prefix in ['__', '_BaseSheet__', '_BaseSheetMetaclass__']:
                if name.startswith(prefix):
                    attrs.pop(name)
                    break
            else:
                # Remove properties and methods
                if inspect.ismethod(value) or isinstance(value, property) or isinstance(value, types.FunctionType):
                    attrs.pop(name)

        # TODO Add check for reserved names

        # Getting columns order number in a table
        # Order number may be specified in model explicitly
        specified_order_numbers = [field.order_number for field in attrs
                                   if isinstance(field, Field) and field.order_number]
        # Get the whole range of order numbers
        order_numbers = list(range(1, max(chain(specified_order_numbers, [len(attrs)])) + 1))
        # Exclude already specified in model
        order_numbers = [i for i in order_numbers if i not in specified_order_numbers]
        # Because we will set them to other columns where order_number is not specified

        columns = []
        for name, value in attrs.items():
            # Define Field
            if isinstance(value, Field):
                field = value
                field.name = name
            else:
                field = Field(name=name, field_type=value, order_number=order_numbers.pop(0))
                setattr(cls, name, field)
            # Set order number
            if not field.order_number:
                field.order_number = order_numbers.pop(0)
            # columns[name] = field
            columns.append(field)
        # Sort by order number
        return sorted(columns, key=lambda x: x.order_number)
