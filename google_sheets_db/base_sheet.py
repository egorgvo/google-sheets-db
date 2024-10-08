from copy import copy, deepcopy
from functools import cached_property
from typing import Union, Optional, Self, Any

import pandas as pd
from deprecation import deprecated

from google_sheets_db import Field, __version__
from google_sheets_db.base_sheet_metaclass import BaseSheetMetaclass
from google_sheets_db.worksheet_mixin import WorksheetMixin


class BaseSheet(WorksheetMixin, metaclass=BaseSheetMetaclass):
    __init_named_row = None
    __init_list_row = None
    __primary_field = None
    # Columns of a sheet
    _columns: list[Field]
    meta = {}

    def __init__(self, *args, _index: int = None, **kwargs):
        self._data = {}
        self._index = _index
        row_dict = self._prepare_row(*args, as_named=True, **kwargs)
        for field in self._columns:
            self[field.name] = row_dict.get(field.name, None)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.pk})'

    def __iter__(self):
        for field in self._columns:
            yield field, getattr(self, field.name)

    def __eq__(self, other):
        for f1, f2 in zip(self, other):
            if f1 != f2:
                return False
        return True

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, item):
        return getattr(self, item)

    def values(self, with_gaps: bool = False) -> list[Any]:
        """Returns values of instance"""

        if with_gaps:
            values = [None for number in range(self.__class__.last_column_number)]
            for field in self._columns:
                values[field.order_number - 1] = self[field.name]
        else:
            return [self[field.name] for field in self._columns]

    @property
    def _columns(self) -> list[Field]:
        """Just an alias for class _columns"""
        return self.__class__._columns  # noqa

    @cached_property
    def _pk_name(self) -> str:
        return self.get_primary_field().name

    @property
    def pk(self) -> Union[int, str]:
        return getattr(self, self._pk_name)

    @pk.setter
    def pk(self, value: Union[int, str]) -> None:
        setattr(self, self._pk_name, value)

    def save(self) -> Self:
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
    def init_named_row(cls) -> dict[str, Any]:
        """
        Init dictionary with default row values

        No API calls.
        """
        if cls.__init_named_row:
            return deepcopy(cls.__init_named_row)
        cls.__init_named_row = {column.name: column.default for column in cls._columns}
        return deepcopy(cls.__init_named_row)

    @classmethod
    def init_list_row(cls) -> list[Any]:
        """
        Init list with default row values

        No API calls.
        """
        if cls.__init_list_row:
            return deepcopy(cls.__init_list_row)
        columns = cls._columns
        result = [None for i in range(cls.last_column_number)]
        for column in columns:
            result[column.order_number - 1] = column.default
        cls.__init_list_row = result
        return deepcopy(cls.__init_list_row)

    @classmethod
    def get_primary_field(cls, raise_exc: bool = False) -> Optional[Field]:
        """Returns primary key name"""
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
    def _get_column_by_name(cls, name: str) -> Field:
        """Returns field by its name"""
        column = [f for f in cls._columns if f.name == name]
        if not column:
            raise Exception(f"Unknown field name: {name}. Sheet schema: {cls.__name__}")
        return column[0]

    @classmethod
    def _get_column_by_order_number(cls, order_number: int, raise_exc: bool = True) -> Optional[Field]:
        column = [f for f in cls._columns if f.order_number == order_number]
        if not column and raise_exc:
            raise Exception(f"Order number is unknown for specified sheet schema: {order_number}, "
                            f"sheet schema: {cls.__name__}.")
        elif not column:
            return None
        return column[0]

    @classmethod
    def get_column_values(cls, order_number: int = None, name: str = 'pk') -> list[Any]:
        """
        Returns all values of column

        Calls API.
        """

        if not order_number:
            if name == 'pk':
                column = cls.get_primary_field()
            else:
                column = cls._get_column_by_name(name)
            order_number = column.order_number

        column_number = cls._sheet_start_column + order_number - 1
        start = cls.cell_a1(column_number, cls._sheet_start_row)
        end = cls.cell_a1(column_number)
        values = cls.get_range_values(f'{start}:{end}')[0]
        return [i[0] if i else None for i in values]

    @classmethod
    def get_table_records(cls) -> list[Self]:
        """
        Returns table data as list of dicts

        Calls API.
        """

        values = cls.get_table_values()
        records = []
        for row in values:
            data = {}
            for field in cls._columns:
                if len(row) >= field.order_number:
                    data[field.name] = row[field.order_number - 1]
            records.append(cls(**data))

        return records

    @classmethod
    def get_table_values(cls) -> list[list[str]]:
        """
        Returns table data as list of lists

        Calls API.
        """
        start = cls.cell_a1(cls._sheet_start_column, cls._sheet_start_row)
        end = cls.cell_a1(cls._sheet_start_column + cls.last_column_number)
        values = cls.get_range_values(f'{start}:{end}')[0]
        return values

    @classmethod
    def count(cls) -> int:
        """
        Get total rows count

        Calls API.
        """
        return len(cls.get_table_values())

    @classmethod
    @deprecated(deprecated_in="1.0.9", removed_in="2.0",
                current_version=__version__,
                details="Use the truncate function instead")
    def clear(cls):
        return cls.truncate()

    @classmethod
    def convert_named_row_to_list(cls, **row) -> list[Any]:
        """Converts named row to a list"""
        result = cls.init_list_row()
        for name, value in row.items():
            result[cls._get_column_by_name(name).order_number - 1] = value
        return result

    @classmethod
    def convert_list_row_to_named(cls, **row) -> dict[str, Any]:
        """Converts list row to dict"""
        result = cls.init_named_row()
        for i, value in enumerate(row):
            column = cls._get_column_by_order_number(i + 1, raise_exc=False)
            if not column:
                continue
            result[column.name] = value
        return result

    @classmethod
    def _prepare_row(cls, *row, pk=None, as_named=False, **fields) -> Union[dict[str, Any], list[Any]]:
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
    def generate_pk(cls, named=False) -> Union[int, dict[str, int]]:
        """
        Generates primary key

        Calls API.
        """
        primary_field = cls.get_primary_field()
        if not primary_field:
            return {} if named else None
        indexes = cls.get_column_values(primary_field.order_number)
        pk = 1
        while True:
            if pk not in indexes and str(pk) not in indexes:
                break
            pk += 1
        if named:
            return {primary_field.name: pk}
        return pk

    @classmethod
    def insert(cls, *row, generate_pk=True, **fields) -> Self:
        """
        Inserts row into a table

        Calls API.
        """
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

        _index = cls._sheet_start_row + cls.count()
        start = cls.cell_a1(cls._sheet_start_column, _index)
        end = cls.cell_a1(cls._sheet_start_column + cls.last_column_number, _index)
        update_data = [{'range': f'{start}:{end}', 'values': [row]}]

        cls._sheet.batch_update(update_data)
        instance = cls(*row, _index=_index, pk=primary_key)
        return instance

    @classmethod
    def insert_many(cls, *rows) -> int:
        """
        Inserts many rows to a table

        Returns next index.
        """
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
    def update_or_insert(cls, filtr=None, update=None, first_only=False) -> list[Self]:
        """Update row or inserts if it doesn't exist"""

        # get dataframe
        values = cls.get_table_values()
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
    def get_row_index_for_pk(cls, pk) -> Optional[int]:
        indexes = cls.get_column_values(cls.get_primary_field().order_number)
        if pk in indexes:
            return indexes.index(pk) + 1
        elif str(pk) in indexes:
            return indexes.index(str(pk)) + 1
        return None

    @classmethod
    def with_pk(cls, pk) -> Self:
        _index = cls.get_row_index_for_pk(pk)
        if _index is None:
            return None

        row_index = cls._sheet_start_row + _index - 1
        start = cls.cell_a1(cls._sheet_start_column, row_index)
        end = cls.cell_a1(cls._sheet_start_column + cls.last_column_number, row_index)
        row = cls.get_range_values(f'{start}:{end}')[0]

        if not row:
            return None
        return cls(*row[0], _index=_index)

    @classmethod
    def _update(cls, *row, index=None, pk=None, **fields):
        if index is None and pk is None:
            raise Exception(f"No key specified for _update method.")

        instance = cls.with_pk(pk)
        if not instance:
            raise Exception(f"No row found for pk {pk}.")
        # init result_row with current row values
        sheet = cls._sheet

        result_row = []
        # and then fill it with new values
        new_values = cls._prepare_row(*row, pk=pk, as_named=True, **fields)
        for column in cls._columns:
            if column.name not in new_values:
                continue
            while len(result_row) < column.order_number:
                result_row.append(None)
            result_row[column.order_number - 1] = new_values[column.name]

        first_cell = cls.cell_a1(cls._sheet_start_column, cls._sheet_start_row + instance._index - 1)

        return sheet.update(first_cell, [result_row])
