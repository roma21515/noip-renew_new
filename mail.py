import json
import logging
import os.path
import re, time

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource

logging.basicConfig(
  level = logging.INFO,
  format = '[%(asctime)s] [%(levelname)s] %(message)s',
  datefmt = '%Y/%m/%d %I:%M:%S'
)

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def loginFlow() -> None:
  flow = InstalledAppFlow.from_client_secrets_file(
    "credentials.json", SCOPES
  )
  creds = flow.run_local_server(port=0)
  with open("token.json", "w") as token:
    token.write(creds.to_json())
  return
  

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
    # If there are no (valid) credentials available, let the user log in.
    if not creds: return logging.error("Token is not available")
    if not creds.valid: return logging.error("Token is invaild")

  # Call the Gmail API
  return build("gmail", "v1", credentials=creds)

def verifyCode(service: Resource, timestamp: int) -> int:
  labelRes = service.users().labels()
  labels = labelRes.list(userId="me").execute().get("labels", [])

  if not labels:
    return print("No labels found.")
  
  logging.debug(f"You have {len(labels)} indexs in your mailbox")
  # for label in labels:
  #   print(label["name"])
  
  msgRes: Resource = service.users().messages()
  allMsg = msgRes.list(userId="me", labelIds=["CATEGORY_UPDATES"], q=f"after:{timestamp}").execute()

  for msgId in allMsg.get("messages", []):
    msg = msgRes.get(userId="me", id=msgId["id"]).execute()
    subject = list(filter(lambda e: e["name"] == "Subject", msg["payload"]["headers"]))

    # Skip mail if subject field not found
    if not len(subject): continue 
    
    # Skip mail if it doesn't match No-IP verification mail pattern
    if not re.match(r"No-IP Verification Code: \d{6}", subject[0]["value"]): continue

    return re.findall(r"\d{6}", subject[0]["value"])[0] # Return matched code

def fetchCode():
  attempts = 0
  now = int(time.time())
  service = buildService()
  if not service:
    logging.error(f"Gmail API service not being built, script will end here.")
    return
  
  logging.info(f"Gmail API service built, start fetching emails...")

  while True:
    attempts += 1
    if attempts > 30:
      logging.warning(f"Failed to get verification code (timeout)")
      return None
    
    logging.info(f"Attempting to get verification code from Gmail API ({attempts})")
    code = verifyCode(service, now)

    if code:
      logging.info(f"The verification code is {code}")
      return code
    
    time.sleep(5) # Sleep for 5 seconds to prevent 429

if __name__ == "__main__": fetchCode()