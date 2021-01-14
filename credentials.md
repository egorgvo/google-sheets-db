INSTRUCTIONS

1. Go to the Google APIs Console: https://console.developers.google.com/
2. Create a new project.
3. Click Enable API. Search for and enable the Google Sheets API.
4. Create credentials for a Web Server to access Application Data.
5. Name the service account and grant it a Project Role of Editor.
6. Download the JSON file.
7. Copy the JSON file to your code directory and rename it to `.credentials.json`.
8. Find the `client_email` inside `.credentials.json` and give it edit rights on your desired spreadsheet.