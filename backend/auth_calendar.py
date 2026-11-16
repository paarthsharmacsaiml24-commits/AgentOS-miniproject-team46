from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
BASE = Path(__file__).resolve().parent
SCOPES = [
    "https://www.googleapis.com/auth/calendar.events"
]
flow = InstalledAppFlow.from_client_secrets_file(
    str(BASE / "credentials.json"),
    SCOPES
)
creds = flow.run_local_server(
    port=0,
    access_type="offline",
    prompt="consent"
)
with open(BASE / "token.json", "w") as token:
    token.write(creds.to_json())
print("Google Calendar authorization successful!")
print("New token saved.")