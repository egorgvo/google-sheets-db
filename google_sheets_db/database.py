import os
import pickle
from os.path import split

import gspread
from google.auth.transport.requests import Request
from oauth2client.service_account import ServiceAccountCredentials


class SpreadSheetDescriptor:

    def __get__(self, instance, owner):
        """Descriptor for retrieving a spreadsheet value."""
        if instance.__spreadsheet:
            return instance.__spreadsheet

        # Otherwise raise an exception
        raise Exception("Spreadsheet is closed.")

    def __set__(self, instance, value):
        """Descriptor for assigning a value to a field in a document."""
        instance.__spreadsheet = value # noqa


class GoogleSheetsDB:

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    spreadsheets = []
    spreadsheet = SpreadSheetDescriptor()

    def __init__(self, spreadsheet_id, *args, credentails_file=None, credentials_pickle=None, **kwargs):
        if not credentials_pickle:
            if credentails_file:
                credentials_pickle = split(credentails_file)[0]
            credentials_pickle += '.credentials.pickle'
        credentials = None
        if os.path.exists(credentials_pickle):
            with open(credentials_pickle, 'rb') as token:
                credentials = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not credentials or credentials.invalid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                credentials = ServiceAccountCredentials.from_json_keyfile_name(credentails_file, self.SCOPES)
            # Save the credentials for the next run
            with open(credentials_pickle, 'wb') as token:
                pickle.dump(credentials, token)

        gc = gspread.authorize(credentials)
        self.spreadsheet_id = spreadsheet_id
        self.spreadsheet = gc.open_by_key(self.spreadsheet_id)
        self.spreadsheets.append(self)

    def close(self):
        self.spreadsheets.remove(self)
        self.spreadsheet = None

    def get_sheet_by_name(self, name):
        return self.spreadsheet.worksheet(name)

    def get_sheets(self):
        return self.spreadsheet.worksheets()

    def create_sheet(self, name, rows=100, cols=20):
        return self.spreadsheet.add_worksheet(title=name, rows=str(rows), cols=str(cols))

    def create_sheet_if_not_exists(self, name, rows=100, cols=20):
        try:
            return self.get_sheet_by_name(name)
        except gspread.WorksheetNotFound:
            return self.create_sheet(name, rows=rows, cols=cols)

    def drop_sheet(self, worksheet):
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
