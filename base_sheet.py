from operator import itemgetter

from field import Field
from google_sheets_db import GoogleSheetsDB


class BaseSheet:
    __spreadsheet = None
    __sheet_name = ''
    __sheet = None
    __columns = []
    meta = {}

    @classmethod
    def _db(cls):
        if cls.__spreadsheet:
            return cls.__spreadsheet

        if cls.meta.get('spreadsheet_id'):
            spreadsheet = [s for s in GoogleSheetsDB.spreadsheets if s.spreadsheet_id == cls.meta['spreadsheet_id']]
            if not spreadsheet:
                raise Exception(f"Spreadsheet {cls.meta['spreadsheet_id']} is not declared.")
            cls.__spreadsheet = spreadsheet[0]
        elif GoogleSheetsDB.spreadsheets:
            cls.__spreadsheet = GoogleSheetsDB.spreadsheets[0]
        else:
            raise Exception("No spreadsheet specified.")
        return cls.__spreadsheet

    @classmethod
    def _sheet_name(cls):
        if cls.__sheet_name:
            return cls.__sheet_name

        cls.__sheet_name = cls.meta['sheet_name'] if cls.meta.get('sheet_name') else cls.__name__
        return cls.__sheet_name

    @classmethod
    def _sheet(cls):
        if cls.__sheet:
            return cls.__sheet

        cls.__sheet = cls._db().get_sheet_by_name(cls._sheet_name())
        return cls.__sheet

    @classmethod
    def _columns(cls):
        if cls.__columns:
            return cls.__columns

        attrs = dict(cls.__dict__.items())
        attrs.pop('__module__', None)
        attrs.pop('__doc__', None)
        attrs.pop('_BaseSheet__spreadsheet', None)
        attrs.pop('_BaseSheet__sheet_name', None)
        fields = []
        for i, field in enumerate(attrs):
            fields.append(Field(field, order_number=i, field_type=getattr(cls, field)))
        fields = sorted(fields, key=lambda x: x.order_number)
        cls.__columns = fields
        return cls.__columns

    @classmethod
    def _get_column_by_name(cls, name):
        column = [f for f in cls._columns() if f.name == name]
        if not column:
            raise Exception(f"Unknown field name: {name}.")
        return column[0]

    @classmethod
    def get_all_records(cls):
        return cls._sheet().get_all_records()

    @classmethod
    def get_all_values(cls):
        return cls._sheet().get_all_values()

    @classmethod
    def get_all_data(cls, as_dicts=False):
        return cls.get_all_records() if as_dicts else cls.get_all_values()

    @classmethod
    def count(cls):
        return len(cls.get_all_values())

    @classmethod
    def clear(cls):
        return cls._sheet().clear()

    @classmethod
    def insert(cls, *row, **fields):
        row = list(row)
        fields_cache = []
        for name, value in fields.items():
            fields_cache.append({
                'order_number': cls._get_column_by_name(name).order_number,
                'value': value
            })
        fields_cache = sorted(fields_cache, key=itemgetter('order_number'))
        for field in fields_cache:
            order_number = field['order_number']
            while len(row) < order_number:
                row.append(None)
            row.insert(order_number, field['value'])
        columns = cls._columns()
        if len(row) > len(columns):
            raise Exception(f"Values length is greater than columns length: {row}.")

        index = int(cls.count()) + 1
        cls._sheet().insert_row(row, index=index)
        return index

    @classmethod
    def insert_many(cls, *rows):
        if len(rows) == 1 and isinstance(rows[0], list) and len(rows[0]) == 1 and isinstance(rows[0][0], list):
            rows = rows[0]
        columns = cls._columns()
        for row in rows:
            if len(row) <= len(columns):
                continue
            raise Exception(f"Values length is greater than columns length: {rows}.")

        index = int(cls.count()) + 1
        cls._sheet().insert_rows(rows, row=index)
        return index
