from unittest import main, TestCase

from google_sheets_db import BaseSheet, PrimaryKey, Field


class Sheet(BaseSheet):
    id = PrimaryKey()
    first_name = str
    last_name = str


class Sheet2(BaseSheet):
    id = PrimaryKey()
    last_name = Field(str, order_number=5)
    first_name = str


class BaseSheetTests(TestCase):

    def test_init_list_row(self):
        row = Sheet.init_list_row()
        self.assertListEqual(row, [None, '', ''])

    def test_init_list_row_append(self):
        row = Sheet.init_list_row()
        row.append(None)
        another_row = Sheet.init_list_row()
        self.assertListEqual(another_row, [None, '', ''])

    def test_init_named_row(self):
        row = Sheet.init_named_row()
        self.assertDictEqual(row, {'id': None, 'first_name': '', 'last_name': ''})

    def test_init_named_row_append(self):
        row = Sheet.init_named_row()
        row['state'] = 'cancelled'
        another_row = Sheet.init_named_row()
        self.assertDictEqual(another_row, {'id': None, 'first_name': '', 'last_name': ''})

    def test_a1_notation(self):
        """Tests getting of A1 notation"""
        a1 = Sheet.cell_a1(2, 1)
        self.assertEqual(a1, "B1")
        a1 = Sheet.cell_a1(4)
        self.assertEqual(a1, "D")

    def test_last_column_number(self):
        """Tests getting of A1 notation"""
        self.assertEqual(Sheet.last_column_number, 3)
        self.assertEqual(Sheet2.last_column_number, 5)


if __name__ == '__main__':
    main()
