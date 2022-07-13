from unittest import main, TestCase

from google_sheets_db import BaseSheet, PrimaryKey


class Sheet(BaseSheet):
    id = PrimaryKey()
    first_name = str
    last_name = str


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


if __name__ == '__main__':
    main()
