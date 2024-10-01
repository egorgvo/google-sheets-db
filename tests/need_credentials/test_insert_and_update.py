import os
from unittest import main, TestCase

from dotenv import load_dotenv

from google_sheets_db import GoogleSheetsDB, BaseSheet, PrimaryKey

load_dotenv()
CREDENTIALS_FILE = os.getenv('CREDENTIALS_FILE')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')


class Лист1(BaseSheet):
    meta = {
        'start_row': 4,
        'start_column': 6
    }
    id = PrimaryKey()
    first_name = str
    last_name = str


class ActiveFieldTests(TestCase):

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass()

        db = GoogleSheetsDB(SPREADSHEET_ID, credentails_file=CREDENTIALS_FILE)

    def test_insert(self):
        primary_field = Лист1.get_primary_field()
        # Get all values of id column
        old_primary_keys = Лист1.get_column_values(order_number=primary_field.order_number)
        instance = Лист1.insert('Name', 'Surname')
        pk = instance.pk
        data = Лист1.with_pk(pk)
        self.assertEqual(data, Лист1(str(pk), 'Name', 'Surname'))
        # Get renewed values of id column
        new_primary_keys = Лист1.get_column_values(order_number=primary_field.order_number)
        # Check that there is new id there
        self.assertListEqual(old_primary_keys + [str(pk)], new_primary_keys)
        Лист1.update_with_pk(pk, 'Петр', 'Васильев')
        # Check new values
        data = Лист1.with_pk(pk)
        self.assertEqual(Лист1(str(pk), 'Петр', 'Васильев'), data)

    def test_save(self):
        # Get all values of id column
        primary_field = Лист1.get_primary_field()
        old_primary_keys = Лист1.get_column_values(order_number=primary_field.order_number)
        # Init instance
        instance = Лист1(first_name='Name', last_name='Surname')
        self.assertIsNone(instance.pk)
        instance.save()
        # Get renewed values of id column
        new_primary_keys = Лист1.get_column_values(order_number=primary_field.order_number)
        # Check that there is new id there
        self.assertListEqual(old_primary_keys + [str(instance.pk)], new_primary_keys)
        # Check new values
        data = Лист1.with_pk(instance.pk)
        self.assertEqual(Лист1(str(instance.pk), 'Name', 'Surname'), data)


if __name__ == '__main__':
    main()
