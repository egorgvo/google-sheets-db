import os
import pickle

import httplib2
from apiclient import discovery
from google.auth.transport.requests import Request
from oauth2client.service_account import ServiceAccountCredentials


class GoogleSheetsDB:

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    SPREADSHEETS = []

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

        http_auth = credentials.authorize(httplib2.Http())
        self.service = discovery.build('sheets', 'v4', http=http_auth)
        self.spreadsheet_id = spreadsheet_id
        self.SPREADSHEETS.append(self)

    def close(self):
        self.SPREADSHEETS.remove(self)

    def spreadsheets(self):
        return self.service.spreadsheets()

    def get_sheets(self):
        spreadsheet = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
        return spreadsheet.get('sheets')

    def get_sheets_names(self):
        return [sheet['properties']['title'] for sheet in self.get_sheets()]

    def get_sheets_map(self, inverted=False):
        if inverted:
            return {sheet['properties']['title']: sheet['properties']['sheetId'] for sheet in self.get_sheets()}
        else:
            return {sheet['properties']['sheetId']: sheet['properties']['title'] for sheet in self.get_sheets()}

    def sheet_exists(self, name):
        return name in self.get_sheets_names()
