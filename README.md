# google-sheets-db
Google Sheets as a database ORM

## Usage example

```python
import os
from dotenv import load_dotenv
from google_sheets_db import GoogleSheetsDB, BaseSheet, PrimaryKey, Field

class Sheet1(BaseSheet):
    id = PrimaryKey()
    first_name = Field(str)
    last_name = str

load_dotenv()
CREDENTIALS_FILE = os.getenv('CREDENTIALS_FILE')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
db = GoogleSheetsDB(SPREADSHEET_ID, credentails_file=CREDENTIALS_FILE)

instance = Sheet1(first_name='Name', last_name='Surname')
instance.save()
```

## Google API Credentials
To use this library you will need Google API credentials (which simply is a json file with Google data).  
To get them use this manual:

[How to get a credentials](credentials.md)

### 1.0.0 (2021-01-14)

- Init version.
