
from datetime import datetime, timezone
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

BASE = Path(__file__).resolve().parent.parent
TOKEN = BASE / "token.json"

def get_upcoming_events():
    creds = Credentials.from_authorized_user_file(str(TOKEN))

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN.write_text(creds.to_json())

    service = build("calendar", "v3", credentials=creds)

    result = service.events().list(
        calendarId="primary",
        timeMin=datetime.now(timezone.utc).isoformat(),
        maxResults=10,
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    return [
        {
            "title": event.get("summary", "Untitled event"),
            "start": event.get("start", {}).get(
                "dateTime",
                event.get("start", {}).get("date")
            )
        }
        for event in result.get("items", [])
    ]
