import logging
from argparse import ArgumentParser

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError

logging.basicConfig(
  level = logging.INFO,
  format = '[%(asctime)s] [%(levelname)s] %(message)s',
  datefmt = '%Y/%m/%d %I:%M:%S'
)

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def main():
  parser = ArgumentParser()
  parser.add_argument("-cred", "--credential", help="Gmail API credential json path", default=".\\credentials.json")
  args = parser.parse_args()

  flow = InstalledAppFlow.from_client_secrets_file(args.credential, SCOPES)
  creds = flow.run_local_server(port=0)

  logging.info("Login requests detected !")
  with open("token.json", "w") as token:
    token.write(creds.to_json())
  logging.info("Your token has been written into current folder.")
  return

if __name__ == "__main__": main()