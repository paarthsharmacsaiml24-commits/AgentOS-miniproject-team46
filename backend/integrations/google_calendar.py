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
    now = datetime.now(timezone.utc)
    end = now.replace(
        month=1, day=1, hour=0, minute=0,
        second=0, microsecond=0
    ).replace(year=now.year + 1)
    result = service.events().list(
        calendarId="primary",
        timeMin=now.isoformat(),
        timeMax=end.isoformat(),
        maxResults=2500,
        singleEvents=True,
        orderBy="startTime"
    ).execute()
    return [
        {
            "id": event.get("id"),
            "title": event.get("summary", "Untitled event"),
            "start": event.get("start", {}).get(
                "dateTime", event.get("start", {}).get("date")
            ),
            "end": event.get("end", {}).get(
                "dateTime", event.get("end", {}).get("date")
            ),
            "description": event.get("description", "")
        }
        for event in result.get("items", [])
    ]
def get_calendar_event(event_id):
    service = get_calendar_service()
    event = service.events().get(
        calendarId="primary",
        eventId=event_id
    ).execute()
    return {
        "id": event.get("id"),
        "title": event.get("summary", "Untitled event"),
        "start": event.get("start", {}).get(
            "dateTime", event.get("start", {}).get("date")
        ),
        "end": event.get("end", {}).get(
            "dateTime", event.get("end", {}).get("date")
        ),
        "description": event.get("description", "")
    }
def create_calendar_event(
    title, date, start_time, duration_minutes, description=""
):
    if not title.strip():
        raise ValueError("Meeting title cannot be empty.")
    if duration_minutes < 5 or duration_minutes > 480:
        raise ValueError("Duration must be between 5 and 480 minutes.")
    start = datetime.strptime(
        f"{date} {start_time}", "%Y-%m-%d %H:%M"
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
def check_calendar_conflicts(start, end, exclude_event_id=None):
    service = get_calendar_service()
    result = service.events().list(
        calendarId="primary",
        timeMin=start.astimezone(timezone.utc).isoformat(),
        timeMax=end.astimezone(timezone.utc).isoformat(),
        maxResults=250,
        singleEvents=True,
        orderBy="startTime"
    ).execute()
    conflicts = []
    for event in result.get("items", []):
        if event.get("id") == exclude_event_id:
            continue
        event_start = event.get("start", {}).get("dateTime")
        event_end = event.get("end", {}).get("dateTime")
        if not event_start or not event_end:
            continue
        existing_start = datetime.fromisoformat(event_start)
        existing_end = datetime.fromisoformat(event_end)
        if start < existing_end and end > existing_start:
            conflicts.append({
                "id": event.get("id"),
                "title": event.get("summary", "Untitled event"),
                "start": event_start,
                "end": event_end
            })
    return conflicts
def update_calendar_event(
    event_id,
    title=None,
    date=None,
    start_time=None,
    duration_minutes=None,
    description=None
):
    service = get_calendar_service()
    event = service.events().get(
        calendarId="primary",
        eventId=event_id
    ).execute()
    if "dateTime" not in event.get("start", {}):
        raise ValueError(
            "Editing all-day events is not supported yet."
        )
    old_start = datetime.fromisoformat(event["start"]["dateTime"])
    old_end = datetime.fromisoformat(event["end"]["dateTime"])
    new_title = title.strip() if title is not None else event.get(
        "summary", "Untitled event"
    )
    if not new_title:
        raise ValueError("Meeting title cannot be empty.")
    if date is not None or start_time is not None:
        current_local = old_start.astimezone(TIMEZONE)
        new_date = date or current_local.strftime("%Y-%m-%d")
        new_time = start_time or current_local.strftime("%H:%M")
        new_start = datetime.strptime(
            f"{new_date} {new_time}", "%Y-%m-%d %H:%M"
        ).replace(tzinfo=TIMEZONE)
    else:
        new_start = old_start
    if duration_minutes is not None:
        if duration_minutes < 5 or duration_minutes > 480:
            raise ValueError(
                "Duration must be between 5 and 480 minutes."
            )
        new_duration = timedelta(minutes=duration_minutes)
    else:
        new_duration = old_end - old_start
    if new_start <= datetime.now(TIMEZONE):
        raise ValueError("Meeting date and time must be in the future.")
    new_end = new_start + new_duration
    conflicts = check_calendar_conflicts(
        new_start, new_end, exclude_event_id=event_id
    )
    if conflicts:
        return {
            "status": "conflict",
            "message": "The selected time overlaps another meeting.",
            "conflicts": conflicts
        }
    event["summary"] = new_title
    event["start"] = {
        "dateTime": new_start.isoformat(),
        "timeZone": "Asia/Kolkata"
    }
    event["end"] = {
        "dateTime": new_end.isoformat(),
        "timeZone": "Asia/Kolkata"
    }
    if description is not None:
        event["description"] = description.strip()
    updated = service.events().update(
        calendarId="primary",
        eventId=event_id,
        body=event
    ).execute()
    return {
        "status": "updated",
        "id": updated.get("id"),
        "title": updated.get("summary"),
        "start": updated.get("start", {}).get("dateTime"),
        "end": updated.get("end", {}).get("dateTime"),
        "link": updated.get("htmlLink")
    }
def delete_calendar_event(event_id):
    service = get_calendar_service()
    service.events().delete(
        calendarId="primary",
        eventId=event_id
    ).execute()
    return {
        "status": "deleted",
        "id": event_id,
        "message": "Meeting successfully deleted."
    }