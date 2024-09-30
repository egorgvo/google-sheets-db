import os
from collections import OrderedDict
from unittest import main, TestCase

from dotenv import load_dotenv

from google_sheets_db import GoogleSheetsDB, BaseSheet, PrimaryKey

load_dotenv()
CREDENTIALS_FILE = os.getenv('CREDENTIALS_FILE')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')


class SheetToDelete(BaseSheet):
    meta = {
        'sheet_name': 'SheetToDelete'
    }
    id = PrimaryKey()
    first_name = str
    last_name = str


class CreateDropTruncateTests(TestCase):

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass()

        cls.db = GoogleSheetsDB(SPREADSHEET_ID, credentails_file=CREDENTIALS_FILE)
        SheetToDelete.create_sheet_if_not_exists()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        SheetToDelete.drop()

    def test_create(self):
        self.assertTrue(SheetToDelete.exists())
        # Add row
        instance = SheetToDelete(first_name='Name', last_name='Surname')
        instance.save()
        # Get renewed values of id column
        values = SheetToDelete.get_table_values()
        self.assertEqual(len(values), 1)
        # Get record
        values = SheetToDelete.get_table_records()
        self.assertEqual(len(values), 1)
        self.assertEqual(values, [OrderedDict(id=str(1), first_name='Name', last_name='Surname')])
        # truncate
        SheetToDelete.truncate()
        values = SheetToDelete.get_all_values()
        self.assertEqual(len(values), 0)
        # drop
        SheetToDelete.drop()
        self.assertFalse(SheetToDelete.exists())
        # create
        SheetToDelete.create_sheet_if_not_exists()
        self.assertTrue(SheetToDelete.exists())


if __name__ == '__main__':
    main()
