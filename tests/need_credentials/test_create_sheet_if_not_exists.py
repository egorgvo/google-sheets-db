import os
from unittest import main, TestCase

from dotenv import load_dotenv
from gspread import WorksheetNotFound

from google_sheets_db import GoogleSheetsDB, BaseSheet

load_dotenv()
CREDENTIALS_FILE = os.getenv('CREDENTIALS_FILE')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')

sheet_name = 'NonexistentSheet'


class CustomSheet(BaseSheet):
    meta = {
        'sheet_name': sheet_name
    }


class CreateSheetIfNotExistsTests(TestCase):

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass()

        cls.db = GoogleSheetsDB(SPREADSHEET_ID, credentails_file=CREDENTIALS_FILE)
        cls.sheet_name = sheet_name

    def setUp(self) -> None:
        super().setUp()

        # we should start from the blank page
        self.delete_test_sheet()

    def tearDown(self) -> None:
        super().setUpClass()
        # let's clean up after us
        self.delete_test_sheet()

    def delete_test_sheet(self):
        try:
            # if the spreadsheet have sheet already
            sheet = self.db.get_sheet_by_name(self.sheet_name)
            # remove
            self.db.drop_sheet(sheet)
        except WorksheetNotFound:
            pass

    def test_pass_if_exists(self):
        self.db.create_sheet(self.sheet_name)
        self.assertTrue(self.db.sheet_exists(name=self.sheet_name))
        self.db.create_sheet_if_not_exists(name=self.sheet_name)
        self.assertTrue(self.db.sheet_exists(name=self.sheet_name))

    def test_create_if_not_exists(self):
        # requests are expensive, so let's test two features at a time
        # test GoogleSheetsDB.sheet_exists
        self.assertFalse(self.db.sheet_exists(name=self.sheet_name))
        # test GoogleSheetsDB.create_sheet_if_not_exists
        self.db.create_sheet_if_not_exists(name=self.sheet_name)
        self.assertTrue(self.db.sheet_exists(name=self.sheet_name))

    def test_create_self_if_not_exists(self):
        # requests are expensive, so let's test two features at a time
        # test BaseSheet.exists
        self.assertFalse(CustomSheet.exists())
        # and BaseSheet.create_sheet_if_not_exists
        CustomSheet.create_sheet_if_not_exists()
        self.assertTrue(CustomSheet.exists())


if __name__ == '__main__':
    main()
