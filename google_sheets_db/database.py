import os
import pickle

import gspread
from google.auth.transport.requests import Request
from oauth2client.service_account import ServiceAccountCredentials


class GoogleSheetsDB:

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    spreadsheets = []

    def __init__(self, spreadsheet_id, *args, credentails_file=None, **kwargs):
        credentials = None
        if os.path.exists('.credentials.pickle'):
            with open('.credentials.pickle', 'rb') as token:
                credentials = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not credentials or credentials.invalid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                credentials = ServiceAccountCredentials.from_json_keyfile_name(credentails_file, self.SCOPES)
            # Save the credentials for the next run
            with open('.credentials.pickle', 'wb') as token:
                pickle.dump(credentials, token)

        gc = gspread.authorize(credentials)
        self.spreadsheet_id = spreadsheet_id
        self.spreadsheet = gc.open_by_key(self.spreadsheet_id)
        self.spreadsheets.append(self)

    def close(self):
        self.spreadsheets.remove(self)

    def get_sheet_by_name(self, name):
        return self.spreadsheet.worksheet(name)

    def get_sheets(self):
        return self.spreadsheet.worksheets()

    def create_sheet(self, name, rows=100, cols=20):
        return self.spreadsheet.add_worksheet(title=name, rows=str(rows), cols=str(cols))

    def delete_sheet(self, worksheet):
        self.spreadsheet.del_worksheet(worksheet)

    def get_sheets_names(self):
        return [sheet.title for sheet in self.get_sheets()]

    def sheet_exists(self, name):
        return name in self.get_sheets_names()

    def get_sheets_map(self, inverted=False):
        if inverted:
            return {sheet.title: sheet.id for sheet in self.get_sheets()}
        else:
            return {sheet.id: sheet.title for sheet in self.get_sheets()}
