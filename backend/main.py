from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from agents.agent_graph import process_command
from agents.scheduler import get_calendar_events
from intelligence.memory import get_history
from intelligence.job_manager import (
    submit_job,
    get_job_status,
    get_all_jobs
)
from integrations.google_calendar import (
    create_calendar_event,
    get_calendar_event,
    update_calendar_event,
    delete_calendar_event
)
app = FastAPI(title="AgentOS API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
class CommandRequest(BaseModel):
    command: str
class MeetingRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    date: str
    start_time: str
    duration_minutes: int = Field(ge=5, le=480)
    description: str = ""
class MeetingUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, max_length=200)
    date: Optional[str] = None
    start_time: Optional[str] = None
    duration_minutes: Optional[int] = Field(default=None, ge=5, le=480)
    description: Optional[str] = None
@app.get("/")
def home():
    return {
        "message": "AgentOS API is running",
        "engine": "LangGraph",
        "background_jobs": True
    }
@app.get("/calendar/events")
def calendar_events():
    try:
        return {"events": get_calendar_events()}
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))
@app.get("/calendar/events/{event_id}")
def calendar_event(event_id: str):
    try:
        return get_calendar_event(event_id)
    except Exception as error:
        raise HTTPException(status_code=404, detail=str(error))
@app.post("/calendar/events")
def add_calendar_event(request: MeetingRequest):
    try:
        event = create_calendar_event(
            title=request.title,
            date=request.date,
            start_time=request.start_time,
            duration_minutes=request.duration_minutes,
            description=request.description
        )
        return {
            "status": "created",
            "message": "Meeting successfully added to Google Calendar.",
            "event": event
        }
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))
@app.put("/calendar/events/{event_id}")
def edit_calendar_event(
    event_id: str,
    request: MeetingUpdateRequest
):
    try:
        result = update_calendar_event(
            event_id=event_id,
            title=request.title,
            date=request.date,
            start_time=request.start_time,
            duration_minutes=request.duration_minutes,
            description=request.description
        )
        if result.get("status") == "conflict":
            raise HTTPException(status_code=409, detail=result)
        return result
    except HTTPException:
        raise
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))
@app.delete("/calendar/events/{event_id}")
def remove_calendar_event(event_id: str):
    try:
        return delete_calendar_event(event_id)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))
@app.post("/command")
def execute_command(request: CommandRequest):
    try:
        if not request.command.strip():
            raise HTTPException(
                status_code=400,
                detail="Please enter a command."
            )
        return process_command(request.command)
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))
@app.post("/jobs")
def create_background_job(request: CommandRequest):
    if not request.command.strip():
        raise HTTPException(
            status_code=400,
            detail="Please enter a command."
        )
    return submit_job(request.command)
@app.get("/jobs")
def get_jobs(limit: int = 20):
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 100."
        )
    return {"jobs": get_all_jobs(limit)}
@app.get("/jobs/{job_id}")
def job_status(job_id: str):
    job = get_job_status(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job
@app.get("/history")
def task_history(limit: int = 10):
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 100."
        )
    return {"history": get_history(limit)}