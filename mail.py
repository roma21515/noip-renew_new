from argparse import ArgumentParser
import json, logging, sys, re, os.path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build, Resource
from google_auth_oauthlib.flow import InstalledAppFlow

# If modifying these scopes, delete the file token.json.
SCOPES = [
  "https://www.googleapis.com/auth/gmail.readonly",
  "https://www.googleapis.com/auth/gmail.modify"
]

def buildService(token: str) -> Resource:
  """Shows basic usage of the Gmail API. Lists the user's Gmail labels."""

  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.

  if not token: 
    if not os.environ.get("token"):
      return logging.error("Environment variable: \"token\" not found")
    
    logging.info("Environment variable: \"token\" found, using it to login...")
    data = json.loads(os.environ["token"])
    creds = Credentials.from_authorized_user_info(data, SCOPES)
  
  elif os.path.exists(token):
    logging.info(f"File: \"{token}\" found, using it to login...")
    creds = Credentials.from_authorized_user_file(token, SCOPES)

  if creds and creds.expired and creds.refresh_token:
    creds.refresh(Request())
  # Call the Gmail API
  return build("gmail", "v1", credentials=creds)

def fetchCode(service: Resource, timestamp: int) -> int:
  msgRes: Resource = service.users().messages()
  allMsg = msgRes.list(userId="me", labelIds=["CATEGORY_UPDATES"], q=f"after:{timestamp}").execute()

  for msgId in map(lambda x: x["id"], allMsg.get("messages", [])):
    msg = msgRes.get(userId="me", id=msgId).execute()
    subject = list(filter(lambda e: e["name"] == "Subject", msg["payload"]["headers"]))

    # Skip mail if subject field not found
    if not len(subject): continue 
    
    # Skip mail if it doesn't match No-IP verification mail pattern
    if not re.match(r"No-IP Verification Code: \d{6}", subject[0]["value"]): continue

    # Move used verification mail to trash 
    msgRes.trash(userId="me", id=msgId).execute()
    
    return re.findall(r"\d{6}", subject[0]["value"])[0] # Return matched code

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
  return 0

if __name__ == "__main__": sys.exit(main())