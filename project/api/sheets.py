"""
If we decide we want to work with the Sheets API later down the road, this
is some sample code that can be used to access the privacy requests spreadsheet.
"""

from __future__ import print_function
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

SPREADSHEET_ID = '1MaSL1WEPzV07H5pZZh8REUU1KuvniHKOrQtE5ak3EpQ'
RANGE_NAME = 'RevData!A1:R'

def main():
    """Shows basic usage of the Sheets API.
    Prints values from a spreadsheet.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    # NOTE: this auth flow needs to run in Chrome, it will fail to connect in Safari
    # https://github.com/googleapis/google-auth-library-python-oauthlib/issues/69
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # This credentials.json file is the OAuth cred for the clientid `request-import-script` in the `voxmedia-data-privacy` project
            # https://console.cloud.google.com/apis/credentials?project=voxmedia-data-dictionary
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=8080)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')
    else:
        for row in values:
            # each column will correspond to an index
            print(row)

if __name__ == '__main__':
    main()
