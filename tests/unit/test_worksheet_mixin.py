from unittest import main, TestCase

from google_sheets_db.base_sheet import WorksheetMixin


class WorksheetMixinTests(TestCase):

    def test_get_all_values(self):
        with self.assertRaisesRegex(Exception, 'No sheet defined.'):
            WorksheetMixin.get_all_values()

    def test_get_column_values(self):
        with self.assertRaisesRegex(Exception, 'No sheet defined.'):
            WorksheetMixin.get_column_values()


if __name__ == '__main__':
    main()
