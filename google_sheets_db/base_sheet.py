import types
from itertools import chain

import pandas as pd
from gspread.utils import rowcol_to_a1

from google_sheets_db import Field, GoogleSheetsDB


class BaseSheet:
    __spreadsheet = None
    __sheet_name = ''
    __sheet = None
    __columns = []
    __init_named_row = None
    __init_list_row = None
    __primary_field = None
    meta = {}

    def __init__(self, *args, **kwargs):
        row_dict = self._prepare_row(*args, as_named=True, **kwargs)
        for field in self._columns():
            setattr(self, field.name, row_dict.get(field.name, field.field_type()))

    def save(self):
        self.update_or_insert({'pk': self.pk}, self._data)

    @property
    def _data(self):
        attrs = dict(self.__dict__.items())
        attrs.pop('__module__', None)
        attrs.pop('__doc__', None)
        attrs.pop('_BaseSheet__spreadsheet', None)
        attrs.pop('_BaseSheet__sheet', None)
        attrs.pop('_BaseSheet__sheet_name', None)
        for name, value in list(attrs.items()):
            if isinstance(value, property) or isinstance(value, types.FunctionType):
                attrs.pop(name)
        return attrs

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
        attrs.pop('_BaseSheet__sheet', None)
        attrs.pop('_BaseSheet__sheet_name', None)
        for name, value in list(attrs.items()):
            if isinstance(value, property) or isinstance(value, types.FunctionType):
                attrs.pop(name)

        fields = []
        specified_order_numbers = [field.order_number for field in attrs
                                   if isinstance(field, Field) and field.order_number]
        order_numbers = list(range(1, max(chain(specified_order_numbers, [len(attrs)])) + 1))
        order_numbers = [i for i in order_numbers if i not in specified_order_numbers]

        for name, value in attrs.items():
            if isinstance(value, Field):
                field = value
                field.name = name
            else:
                field = Field(name=name, field_type=value, order_number=order_numbers.pop(0))
            if not field.order_number:
                field.order_number = order_numbers.pop(0)
            fields.append(field)
        cls.__columns = sorted(fields, key=lambda x: x.order_number)
        return cls.__columns

    @classmethod
    def init_named_row(cls):
        if cls.__init_named_row:
            return cls.__init_named_row
        columns = cls._columns()
        cls.__init_named_row = {column.name: column.field_type() for column in columns}
        return cls.__init_named_row

    @classmethod
    def init_list_row(cls):
        if cls.__init_list_row:
            return cls.__init_list_row
        columns = cls._columns()
        result = [None for i in range(columns[-1].order_number)]
        for column in columns:
            result[column.order_number - 1] = column.field_type()
        cls.__init_list_row = result
        return cls.__init_list_row

    @classmethod
    def get_primary_field(cls, raise_exc=False):
        if cls.__primary_field:
            return cls.__primary_field
        column = [f for f in cls._columns() if f.primary_key]
        if raise_exc and not column:
            raise Exception(f"Primary key is not specified.")
        if len(column) > 1:
            raise Exception(f"More than one primary keys specified. "
                            f"Library does not work with more than one primary fields yet.")
        cls.__primary_field = column[0]
        return cls.__primary_field

    @classmethod
    def _get_column_by_name(cls, name):
        column = [f for f in cls._columns() if f.name == name]
        if not column:
            raise Exception(f"Unknown field name: {name}. Sheet schema: {cls.__name__}")
        return column[0]

    @classmethod
    def _get_column_by_order_number(cls, order_number, raise_exc=True):
        column = [f for f in cls._columns() if f.order_number == order_number]
        if not column and raise_exc:
            raise Exception(f"Order number is unknown for specified sheet schema: {order_number}, "
                            f"sheet schema: {cls.__name__}.")
        elif not column:
            return None
        return column[0]

    @classmethod
    def get_column_values(cls, name=None, order_number=None):
        if not name and not order_number:
            raise Exception(f"Not name nor order_number specified for get_column_values method.")
        if not order_number:
            column = cls._get_column_by_name(name)
            order_number = column.order_number
        return cls._sheet().col_values(order_number)

    @classmethod
    def get_all_values(cls):
        return cls._sheet().get_all_values()

    @classmethod
    def get_all_records(cls):
        values = cls.get_all_values()
        names = [f.name for f in cls._columns()]
        return [dict(zip(names, value)) for value in values]

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
    def convert_named_row_to_list(cls, **row):
        result = cls.init_list_row()
        for name, value in row.items():
            result[cls._get_column_by_name(name).order_number - 1] = value
        return result

    @classmethod
    def convert_list_row_to_named(cls, **row):
        result = cls.init_named_row()
        for i, value in enumerate(row):
            column = cls._get_column_by_order_number(i + 1, raise_exc=False)
            if not column:
                continue
            result[column.name] = value
        return result

    @classmethod
    def _prepare_row(cls, *row, pk=None, as_named=False, **fields):
        row = list(row)
        columns = cls._columns()

        # if pk specified - put it in fields
        if pk and len(columns) > len(fields) + len(row):
            pk_key = cls.get_primary_field()
            if pk_key.name not in fields:
                fields[pk_key.name] = pk

        for i, column in enumerate(columns):
            if not row:
                break
            if column.name in fields:
                continue
            fields[column.name] = row.pop(0)
        if row:
            raise Exception(f"Values length is greater than columns length: {row}.")

        if as_named:
            return fields
        return cls.convert_named_row_to_list(**fields)

    @classmethod
    def generate_index(cls, named=False):
        primary_field = cls.get_primary_field()
        if not primary_field:
            return {} if named else None
        indexes = cls.get_column_values(order_number=primary_field.order_number)
        pk = 100
        while True:
            if pk not in indexes and str(pk) not in indexes:
                break
            pk += 1
        if named:
            return {primary_field.name: pk}
        else:
            return pk

    @classmethod
    def insert(cls, *row, generate_index=True, **fields):
        primary_field = cls.get_primary_field()
        if primary_field.name not in fields and len(row) < len(cls._columns()) and generate_index:
            fields.update(cls.generate_index(named=True))
        row = cls._prepare_row(*row, **fields)
        if primary_field and not row[primary_field.order_number - 1]:
            row[primary_field.order_number - 1] = cls.generate_index()
        elif not generate_index and primary_field and row[primary_field.order_number - 1]:
            indexes = cls.get_column_values(primary_field.order_number)
            if row[primary_field.order_number - 1] in indexes or str(row[primary_field.order_number - 1]) in indexes:
                raise Exception(f"Primary key is not unique: {cls.convert_list_row_to_named(row)}.")

        primary_key = row[primary_field.order_number - 1] if primary_field else None

        index = int(cls.count()) + 1
        cls._sheet().insert_row(row, index=index)
        return index, primary_key

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

    @classmethod
    def update_or_insert(cls, filtr=None, update=None, first_only=False):
        # get dataframe
        values = cls.get_all_values()
        columns_names = [c.name for c in cls._columns()]
        for row in values:
            row.extend([None] * (len(columns_names) - len(row)))
        dataframe = pd.DataFrame(values, columns=columns_names)
        # filter dataframe
        pk = cls.get_primary_field()
        if 'pk' in filtr:
            filtr[pk.name] = filtr.pop('pk')
        for name, value in filtr.items():
            # TODO Реализовать поиск с учетом типа поля
            dataframe = dataframe[dataframe[name] == str(value)]
        rows = []
        for i, row in dataframe.iterrows():
            rows.append(cls.update_with_pk(row[pk.name], **update))
            if first_only:
                break
        if not rows:
            filtr.update(update)
            rows = [cls.insert(**filtr)]
        return rows

    @classmethod
    def update_with_index(cls, index, *row, **fields):
        return cls._update(index=index, *row, **fields)

    @classmethod
    def update_with_pk(cls, pk, *row, **fields):
        return cls._update(pk=pk, *row, **fields)

    @classmethod
    def get_row_index_for_pk(cls, pk):
        indexes = cls.get_column_values(order_number=cls.get_primary_field().order_number)
        if pk in indexes:
            return indexes.index(pk) + 1
        elif str(pk) in indexes:
            return indexes.index(str(pk)) + 1
        return None

    @classmethod
    def get_row_with_pk(cls, pk):
        index = cls.get_row_index_for_pk(pk)
        if index is None:
            return None
        return cls._sheet().row_values(index)

    @classmethod
    def with_pk(cls, pk):
        row = cls.get_row_with_pk(pk)
        if not row:
            return None
        return cls(*row)

    @classmethod
    def _update(cls, *row, index=None, pk=None, **fields):
        if index is None and pk is None:
            raise Exception(f"No key specified for _update method.")

        index = cls.get_row_index_for_pk(pk)
        if not index:
            raise Exception(f"No row found for pk {pk}.")
        # init result_row with current row values
        sheet = cls._sheet()
        result_row = sheet.row_values(index)

        # and then fill it with new values
        new_values = cls._prepare_row(*row, pk=pk, as_named=True, **fields)
        for column in cls._columns():
            if column.name not in new_values:
                continue
            while len(result_row) < column.order_number:
                result_row.append(None)
            result_row[column.order_number - 1] = new_values[column.name]

        first_cell = rowcol_to_a1(index, 1)
        return sheet.update(first_cell, [result_row])

    @property
    def pk(self):
        pk_field = self.get_primary_field()
        return getattr(self, pk_field.name)
