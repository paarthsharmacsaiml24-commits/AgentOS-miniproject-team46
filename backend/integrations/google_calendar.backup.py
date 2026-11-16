from datetime import datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
BASE = Path(__file__).resolve().parent.parent
TOKEN = BASE / "token.json"
TIMEZONE = ZoneInfo("Asia/Kolkata")
def get_calendar_service():
    creds = Credentials.from_authorized_user_file(str(TOKEN))
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN.write_text(creds.to_json())
    return build("calendar", "v3", credentials=creds)
def get_upcoming_events():
    service = get_calendar_service()
    now = datetime.now().astimezone()
    end = now.replace(
        month=1, day=1, hour=0, minute=0,
        second=0, microsecond=0
    ).replace(year=now.year + 1)
    result = service.events().list(
        calendarId="primary",
        timeMin=datetime.now(timezone.utc).isoformat(),
        timeMax=end.astimezone(timezone.utc).isoformat(),
        maxResults=2500,
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
def create_calendar_event(title, date, start_time, duration_minutes, description=""):
    if not title.strip():
        raise ValueError("Meeting title cannot be empty.")

    if duration_minutes < 5 or duration_minutes > 480:
        raise ValueError("Duration must be between 5 and 480 minutes.")
    start = datetime.strptime(
        f"{date} {start_time}",
        "%Y-%m-%d %H:%M"
    ).replace(tzinfo=TIMEZONE)
    if start <= datetime.now(TIMEZONE):
        raise ValueError("Meeting date and time must be in the future.")
    end = start + timedelta(minutes=duration_minutes)
    service = get_calendar_service()
    event = {
        "summary": title.strip(),
        "description": description.strip(),
        "start": {
            "dateTime": start.isoformat(),
            "timeZone": "Asia/Kolkata"
        },
        "end": {
            "dateTime": end.isoformat(),
            "timeZone": "Asia/Kolkata"
        }
    }
    created = service.events().insert(
        calendarId="primary",
        body=event
    ).execute()
    return {
        "id": created.get("id"),
        "title": created.get("summary"),
        "start": created.get("start", {}).get("dateTime"),
        "end": created.get("end", {}).get("dateTime"),
        "link": created.get("htmlLink")
    }