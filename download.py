from __future__ import print_function

import os.path
import sys, io
import pickle as pkl

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
SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive.metadata',
]


def listdir(service, folder_id, get_files=False, get_folders=False):
    """Search file in drive location

    Load pre-authorized user credentials from the environment.
    TODO(developer) - See https://developers.google.com/identity
    for guides on implementing OAuth2 for the application.
    """
    assert get_files or get_folders
    if get_files:
        # payload = "mimeType='application/vnd.google-apps.file'"
        payload = f"parents in '{folder_id}' and mimeType!='application/vnd.google-apps.folder' and trashed=false"
    elif get_folders:
        payload = f"parents in '{folder_id}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    try:
        # create drive api client
        files = {}
        page_token = None
        while True:
            # pylint: disable=maybe-no-member
            response = service.files().list(q=payload,
                                            spaces='drive',
                                            fields='nextPageToken, '
                                                   'files(id, name)',
                                            pageToken=page_token).execute()
            for file in response.get('files', []):
                # Process change
                #print(F'Found file: {file.get("name")}, {file.get("id")}')
                files[file.get("name")] = file.get("id")
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break

    except HttpError as error:
        print(F'An error occurred: {error}')
        files = {}

    return files

def listdir_recursive(service, folder_id, folder_name):
    files = listdir(service, folder_id, get_files=True)
    folders = listdir(service, folder_id, get_folders=True)
    record = {
        "id": folder_id, 
        "name": folder_name,
        "files": files,
        "folders": [listdir_recursive(service, fid, fname) for fname,fid in folders.items()]
    }
    return record

def refresh_creds():
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
    except Exception as e:
        raise e
    return service

def get_file_type(file_id):
    request = service.files().get_media(fileId=file_id)
    mimeType

def download_file(service, file_id, save_path):
    if os.path.exists(save_path):
        print(" [*] Found existing download at {}".format(save_path))
    try:
        request = service.files().get_media(fileId=file_id)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        pbar = tqdm(total=1000)
        progress = 0
        with open(save_path, 'wb') as fp:
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
        print(f'An error occurred: {error}')
        if os.path.exists(save_path):
            os.remove(save_path)
        raise error

def download_recursive(service, hierarchy, rel_path):
    for fname,fid in hierarchy["files"].items():
        fpath = os.path.join(rel_path, fname)
        download_file(service, fid, fpath)
    for folder_obj in hierarchy["folders"]:
        fname = folder_obj["name"]
        fpath = os.path.join(rel_path, fname)
        os.makedirs(fpath, exist_ok=True)
        download_recursive(service, folder_obj, fpath)

def pretty_print(hierarchy, depth=0, max_num=3):
    lf = len(hierarchy["files"])
    ld = len(hierarchy["folders"])
    prec = "\t" * depth
    for i, (fn, fid) in enumerate(hierarchy["files"].items()):
        print("{} - {} [{}]".format(prec, fn, fid))
        if i >= max_num:
            print("{} (omit {} files)".format(prec, lf-max_num))
            break
    for i, fobj in enumerate(hierarchy["folders"]):
        print("{} + {} [{}]".format(prec, fobj["name"], fobj["id"]))
        pretty_print(fobj, depth+1, max_num=max_num)
        #if i >= max_num:
        #    print("{} (omit {} files)".format(prec, ld-max_num))
        #    break

def main():
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    service = refresh_creds()
    file_id = sys.argv[1]
    folder_root = sys.argv[2]
    hierarchy = listdir_recursive(service, file_id, folder_root)

    if len(hierarchy["files"]) == 0 and len(hierarchy["folders"]) == 0:
        print(" [*] Download in single file mode!")
        download_file(service, file_id, folder_root)
    else:
        print(" [*] Download in folder mode!")
        pretty_print(hierarchy)
        while True:
            response = input("Start downloading? (Y/N)")
            if response[0].lower() == "y":
                break
            elif response[0].lower() == "n":
                print(" [*] Quit with repond no...")
                exit()
            else:
                print("Respond {} is not yes/no!".format(response))
        os.makedirs(folder_root, exist_ok=True)
        download_recursive(service, hierarchy, folder_root)

if __name__ == '__main__':
    main()

