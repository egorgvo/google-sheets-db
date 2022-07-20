from copy import copy, deepcopy
from functools import cached_property

import pandas as pd
from deprecation import deprecated
from gspread.utils import rowcol_to_a1

from google_sheets_db import Field, __version__
from google_sheets_db.base_sheet_metaclass import BaseSheetMetaclass
from google_sheets_db.worksheet_mixin import WorksheetMixin


class BaseSheet(WorksheetMixin, metaclass=BaseSheetMetaclass):
    __init_named_row = None
    __init_list_row = None
    __primary_field = None
    meta = {}

    def __init__(self, *args, **kwargs):
        self._data = {}
        self._index = kwargs.pop('_index', None)
        row_dict = self._prepare_row(*args, as_named=True, **kwargs)
        for field in self._columns:
            setattr(self, field.name, row_dict.get(field.name, None))

    def __repr__(self):
        return f'{self.__class__.__name__}({self.pk})'

    @property
    def _columns(self) -> list[Field]:
        """Just an alias for class _columns"""
        return self.__class__._columns  # noqa

    @cached_property
    def _pk_name(self):
        return self.get_primary_field().name

    @property
    def pk(self):
        return getattr(self, self._pk_name)

    @pk.setter
    def pk(self, value):
        setattr(self, self._pk_name, value)

    def save(self):
        update = copy(self._data)
        pk = self.pk
        if pk is None:
            pk = self.generate_pk()
            update.pop(self._pk_name, None)
        self.update_or_insert({self._pk_name: pk}, update=update)
        self.pk = pk
        # TODO init _index too
        return self

    @classmethod
    def init_named_row(cls):
        if cls.__init_named_row:
            return deepcopy(cls.__init_named_row)
        cls.__init_named_row = {column.name: column.default for column in cls._columns}
        return deepcopy(cls.__init_named_row)

    @classmethod
    def init_list_row(cls):
        if cls.__init_list_row:
            return deepcopy(cls.__init_list_row)
        columns = cls._columns
        result = [None for i in range(columns[-1].order_number)]
        for column in columns:
            result[column.order_number - 1] = column.default
        cls.__init_list_row = result
        return deepcopy(cls.__init_list_row)

    @classmethod
    def get_primary_field(cls, raise_exc=False):
        if cls.__primary_field:
            return cls.__primary_field
        column = [f for f in cls._columns if f.primary_key]
        if raise_exc and not column:
            raise Exception(f"Primary key is not specified.")
        elif not column:
            return None
        if len(column) > 1:
            raise Exception(f"More than one primary keys specified. "
                            f"Library does not work with more than one primary fields yet.")
        cls.__primary_field = column[0]
        return cls.__primary_field

    @classmethod
    def _get_column_by_name(cls, name):
        column = [f for f in cls._columns if f.name == name]
        if not column:
            raise Exception(f"Unknown field name: {name}. Sheet schema: {cls.__name__}")
        return column[0]

    @classmethod
    def _get_column_by_order_number(cls, order_number, raise_exc=True):
        column = [f for f in cls._columns if f.order_number == order_number]
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
        return super().get_column_values(order_number)

    @classmethod
    def get_all_records(cls):
        values = cls.get_all_values()
        names = [f.name for f in cls._columns]
        return [dict(zip(names, value)) for value in values]

    @classmethod
    def get_all_data(cls, as_dicts=False):
        return cls.get_all_records() if as_dicts else cls.get_all_values()

    @classmethod
    def count(cls):
        return len(cls.get_all_values())

    @classmethod
    @deprecated(deprecated_in="1.0.9", removed_in="2.0",
                current_version=__version__,
                details="Use the truncate function instead")
    def clear(cls):
        return cls.truncate()

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

        # if pk specified - put it in fields
        if pk and len(cls._columns) > len(fields) + len(row):
            pk_key = cls.get_primary_field()
            if pk_key.name not in fields:
                fields[pk_key.name] = pk

        for i, column in enumerate(cls._columns):
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
    def generate_pk(cls, named=False):
        primary_field = cls.get_primary_field()
        if not primary_field:
            return {} if named else None
        indexes = cls.get_column_values(order_number=primary_field.order_number)
        pk = 1
        while True:
            if pk not in indexes and str(pk) not in indexes:
                break
            pk += 1
        if named:
            return {primary_field.name: pk}
        return pk

    @classmethod
    def insert(cls, *row, generate_pk=True, **fields):
        primary_field = cls.get_primary_field()
        if primary_field.name not in fields and len(row) < len(cls._columns) and generate_pk:
            fields.update(cls.generate_pk(named=True))
        row = cls._prepare_row(*row, **fields)
        if primary_field and not row[primary_field.order_number - 1]:
            row[primary_field.order_number - 1] = cls.generate_pk()
        elif not generate_pk and primary_field and row[primary_field.order_number - 1]:
            indexes = cls.get_column_values(primary_field.order_number)
            if row[primary_field.order_number - 1] in indexes or str(row[primary_field.order_number - 1]) in indexes:
                raise Exception(f"Primary key is not unique: {cls.convert_list_row_to_named(row)}.")

        primary_key = row[primary_field.order_number - 1] if primary_field else None

        _index = int(cls.count()) + 1
        cls._sheet.insert_row(row, index=_index)
        return cls(*row, _index=_index, pk=primary_key)

    @classmethod
    def insert_many(cls, *rows):
        if len(rows) == 1 and isinstance(rows[0], list) and len(rows[0]) == 1 and isinstance(rows[0][0], list):
            rows = rows[0]
        columns = cls._columns
        for row in rows:
            if len(row) <= len(columns):
                continue
            raise Exception(f"Values length is greater than columns length: {rows}.")

        index = int(cls.count()) + 1
        cls._sheet.insert_rows(rows, row=index)
        return index

    @classmethod
    def update_or_insert(cls, filtr=None, update=None, first_only=False):
        # get dataframe
        values = cls.get_all_values()
        columns_names = [c.name for c in cls._columns]
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
        return cls._sheet.row_values(index)

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
        sheet = cls._sheet
        result_row = sheet.row_values(index)

        # and then fill it with new values
        new_values = cls._prepare_row(*row, pk=pk, as_named=True, **fields)
        for column in cls._columns:
            if column.name not in new_values:
                continue
            while len(result_row) < column.order_number:
                result_row.append(None)
            result_row[column.order_number - 1] = new_values[column.name]

        first_cell = rowcol_to_a1(index, 1)
        return sheet.update(first_cell, [result_row])
