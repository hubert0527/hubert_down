# hubert_down

I am gonna let you down.

## How to use
```
python download.py <google_drive_id> <output_filename>
```

## Prerequirements
Note: Step 3-4 needs to be done again after the credential is expired (~1 hour?). But you can run many downloading jobs simultaneously before it expires.

1. Install: `pip install tqdm google-api-python-client google_auth_oauthlib` 
2. Enable OAuth2 in your account: 
    - I forgot the exact flow, something like: create project -> enable google drive api -> create credential (OAuth client ID & desktop app) -> download credential json file (something started with `{"installed":{"client_id":"`).
    - https://www.youtube.com/watch?v=1y0-IfRW114&ab_channel=MafiaCodes
    - https://developers.google.com/identity/protocols/oauth2
    - https://developers.google.com/drive/api/guides/enable-drive-api
3. Save your credential as "credentials.json" alongside this script.
4. Run the download.py script. It will try to open up a local browser window for you to log into your google account.
    - If you are working remotely on a server, you can copy the url shown in the terminal, paste it on your local PC, then login to authenticate. It will show permission denied error after you log in. Welp, you can then check the communication port (it is randomly generated, let's say the port is 9487) on the url, then ssh forward with ` ssh -L 9487:localhost:9487 <username>@<ip-of-your-server>`. Then refresh the page, it should show the authentication is completed.
5. Your download starts now!


