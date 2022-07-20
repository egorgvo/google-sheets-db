import os
from unittest import main, TestCase

from dotenv import load_dotenv

from google_sheets_db import GoogleSheetsDB

load_dotenv()
CREDENTIALS_FILE = os.getenv('CREDENTIALS_FILE')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')


class DBCloseTests(TestCase):

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass()

        cls.db = GoogleSheetsDB(SPREADSHEET_ID, credentails_file=CREDENTIALS_FILE)

    def test_close(self):
        self.db.close()
        with self.assertRaisesRegex(Exception, 'Spreadsheet is closed.'):
            self.db.get_sheets()


if __name__ == '__main__':
    main()
