from __future__ import print_function

import os.path
import sys, io

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

from tqdm import tqdm

# If modifying these scopes, delete the file token.json.
#SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']
#SCOPES = 'https://www.googleapis.com/auth/drive.file'
SCOPES = ['https://www.googleapis.com/auth/drive.file',
            'https://www.googleapis.com/auth/drive',
                'https://www.googleapis.com/auth/drive.file',
                    'https://www.googleapis.com/auth/drive.metadata'
]


def main():
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('drive', 'v3', credentials=creds)

        file_id = sys.argv[1]
        request = service.files().get_media(fileId=file_id)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        pbar = tqdm(total=1000)
        progress = 0
        with open(sys.argv[2], 'wb') as fp:
            while done is False:
                try:
                    status, done = downloader.next_chunk()
                except Exception as e:
                    print(" [!] Exception:", str(e))
                    continue
                new_progress = int(status.progress() * 1000)
                if new_progress > progress:
                    pbar.update(new_progress - progress)
                    progress = new_progress
                #print(F'Download {int(status.progress() * 100)}.')

                file.seek(0)
                fp.write(file.getbuffer())

                file.seek(0)
                file.truncate(0)

    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f'An error occurred: {error}')


if __name__ == '__main__':
    main()
