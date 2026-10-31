
from fastapi import FastAPI
from integrations.google_calendar import get_upcoming_events

app = FastAPI(title="AgentOS")

@app.get("/")
def home():
    return {"message": "AgentOS API is running"}

@app.get("/calendar/events")
def calendar_events():
    return {"events": get_upcoming_events()}
