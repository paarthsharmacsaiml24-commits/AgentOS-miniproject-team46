import { useState, useEffect } from "react";
import "./App.css";
const API = "http://127.0.0.1:8000";
const emptyMeeting = {
  title: "",
  date: "",
  start_time: "",
  duration_minutes: 60,
  description: ""
};
export default function App() {
  const [command, setCommand] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [copyMessage, setCopyMessage] = useState("");
  const [showMeetingForm, setShowMeetingForm] = useState(false);
  const [meeting, setMeeting] = useState(emptyMeeting);
  const [meetingPreview, setMeetingPreview] = useState(false);
  const [calendarEvents, setCalendarEvents] = useState([]);
  const [calendarLoading, setCalendarLoading] = useState(false);
  const [calendarError, setCalendarError] = useState("");
  const [editingEvent, setEditingEvent] = useState(null);
  const [editMeeting, setEditMeeting] = useState(emptyMeeting);
  const [editLoading, setEditLoading] = useState(false);
  useEffect(() => {
    loadCalendarEvents();
  }, []);
  function updateMeeting(e) {
    setMeeting({
      ...meeting,
      [e.target.name]: e.target.value
    });
  }
  function updateEditMeeting(e) {
    setEditMeeting({
      ...editMeeting,
      [e.target.name]: e.target.value
    });
  }
  async function loadCalendarEvents() {
    setCalendarLoading(true);
    setCalendarError("");
    try {
      const response = await fetch(`${API}/calendar/events`);
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Unable to load calendar events.");
      }
      setCalendarEvents(Array.isArray(data) ? data : []);
    } catch (err) {
      setCalendarError(err.message || "Unable to connect to Google Calendar.");
    } finally {
      setCalendarLoading(false);
    }
  }
  async function runCommand(e) {
    e.preventDefault();
    if (!command.trim() || loading) return;
    setError("");
    setResult(null);
    setMeetingPreview(false);
    const submittedCommand = command.trim();
    const normalized = submittedCommand.toLowerCase();
    setCommand("");
    if (
      normalized === "schedule a meeting" ||
      normalized === "schedule meeting" ||
      normalized === "create a meeting" ||
      normalized === "create meeting" ||
      normalized === "add a meeting"
    ) {
      setShowMeetingForm(true);
      return;
    }
    setShowMeetingForm(false);
    setLoading(true);
    try {
      const response = await fetch(`${API}/jobs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command: submittedCommand })
      });
      const job = await response.json();
      if (!response.ok) {
        throw new Error(job.detail || "Unable to submit command.");
      }
      let currentJob = job;
      for (let i = 0; i < 120; i++) {
        if (
          currentJob.status === "completed" ||
          currentJob.status === "failed"
        ) break;
        await new Promise(resolve => setTimeout(resolve, 1000));
        const statusResponse = await fetch(
          `${API}/jobs/${job.job_id}`
        );
        currentJob = await statusResponse.json();
        if (!statusResponse.ok) {
          throw new Error(currentJob.detail || "Unable to get results.");
        }
      }
      if (currentJob.status === "completed") {
        setResult(currentJob.result);
        if (currentJob.result?.intent === "calendar") {
          loadCalendarEvents();
        }
      } else {
        setError(currentJob.error || "The command is taking too long.");
      }
    } catch (err) {
      setError(err.message || "Unable to connect to AgentOS.");
    } finally {
      setLoading(false);
    }
  }
  async function confirmMeeting() {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${API}/calendar/events`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...meeting,
          duration_minutes: Number(meeting.duration_minutes)
        })
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : JSON.stringify(data.detail || "Unable to create meeting.")
        );
      }
      setMeetingPreview(false);
      setShowMeetingForm(false);
      setMeeting(emptyMeeting);
      setCommand("");
      await loadCalendarEvents();
    } catch (err) {
      setError(err.message || "Unable to create calendar event.");
    } finally {
      setLoading(false);
    }
  }
  function openEditForm(event) {
    const start = new Date(event.start);
    const end = new Date(event.end);
    if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
      setCalendarError("This event has an invalid date and cannot be edited.");
      return;
    }
    const date = [
      start.getFullYear(),
      String(start.getMonth() + 1).padStart(2, "0"),
      String(start.getDate()).padStart(2, "0")
    ].join("-");
    const startTime = [
      String(start.getHours()).padStart(2, "0"),
      String(start.getMinutes()).padStart(2, "0")
    ].join(":");
    const duration = Math.max(
      5,
      Math.round((end.getTime() - start.getTime()) / 60000)
    );
    setEditMeeting({
      title: event.title || "",
      date,
      start_time: startTime,
      duration_minutes: Math.min(duration, 480),
      description: event.description || ""
    });
    setEditingEvent(event);
    setCalendarError("");
  }
  async function saveEditedMeeting(e) {
    e.preventDefault();
    if (!editingEvent || editLoading) return;
    setEditLoading(true);
    setCalendarError("");
    try {
      const response = await fetch(
        `${API}/calendar/events/${encodeURIComponent(editingEvent.id)}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            ...editMeeting,
            duration_minutes: Number(editMeeting.duration_minutes)
          })
        }
      );
      const data = await response.json();
      if (!response.ok) {
        const detail = data.detail;
        if (response.status === 409) {
          const message =
            typeof detail === "string"
              ? detail
              : detail?.message ||
                "This time conflicts with another calendar event.";
          throw new Error(`Scheduling conflict: ${message}`);
        }
        throw new Error(
          typeof detail === "string"
            ? detail
            : JSON.stringify(detail || "Unable to update meeting.")
        );
      }
      setEditingEvent(null);
      await loadCalendarEvents();
    } catch (err) {
      setCalendarError(err.message || "Unable to update meeting.");
    } finally {
      setEditLoading(false);
    }
  }
  async function deleteMeeting(event) {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${event.title}" from Google Calendar?`
    );
    if (!confirmed) return;
    setCalendarError("");
    try {
      const response = await fetch(
        `${API}/calendar/events/${encodeURIComponent(event.id)}`,
        { method: "DELETE" }
      );
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : JSON.stringify(data.detail || "Unable to delete meeting.")
        );
      }
      if (editingEvent?.id === event.id) {
        setEditingEvent(null);
      }
      await loadCalendarEvents();
    } catch (err) {
      setCalendarError(err.message || "Unable to delete meeting.");
    }
  }
  async function copyDraft() {
    if (!result?.draft) return;
    const draft = result.draft;
    const text = [
      `To: ${draft.recipient || "Not specified"}`,
      `Subject: ${draft.subject || "No subject"}`,
      "",
      draft.body || ""
    ].join("\n");
    try {
      await navigator.clipboard.writeText(text);
      setCopyMessage("Draft copied to clipboard.");
    } catch {
      setCopyMessage("Unable to copy draft.");
    }
  }
  function formatDate(date) {
    return new Date(date).toLocaleString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hour12: true
    });
  }
  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-icon">A</span> AgentOS
        </div>
        <span className="status"><span /> SYSTEM INTERFACE</span>
      </header>
      <main className="dashboard">
        <section className="hero">
          <span className="eyebrow">YOUR PERSONAL AI WORKSPACE</span>
          <h1>
            One command.<br />
            <span>Multiple possibilities.</span>
          </h1>
          <p>
            Coordinate your tasks and applications through one intelligent assistant.
          </p>
        </section>
        <section className="command-card">
          <label htmlFor="command">
            What would you like AgentOS to do?
          </label>
          <form onSubmit={runCommand}>
            <input
              id="command"
              value={command}
              onChange={e => setCommand(e.target.value)}
              placeholder="e.g. Schedule a meeting"
              disabled={loading}
            />
            <button disabled={loading || !command.trim()}>
              {loading ? "Processing..." : "Run Command"}
              {!loading && <span> →</span>}
            </button>
          </form>
          <div className="suggestions">
            <span>TRY</span>
            <button type="button" onClick={() => setCommand("Show my upcoming meetings")}>
              Upcoming meetings
            </button>
            <button type="button" onClick={() => setCommand("Show my calendar events")}>
              Calendar events
            </button>
            <button type="button" onClick={() => setCommand("Schedule a meeting")}>
              Schedule a meeting
            </button>
            <button
              type="button"
              onClick={() => setCommand("Draft an email to test@example.com subject: Meeting reschedule message: Can we move our meeting to Friday?")}
            >
              Draft an email
            </button>
            <button type="button" onClick={() => setCommand("List files in my project")}>
              Search project files
            </button>
          </div>
        </section>
        {showMeetingForm && (
          <section className="result-card">
            <div className="result-heading">
              <div>
                <span className="eyebrow">GOOGLE CALENDAR</span>
                <h2>Schedule a Meeting</h2>
              </div>
              <span className="result-badge">New event</span>
            </div>
            {!meetingPreview ? (
              <form
                className="meeting-form"
                onSubmit={e => {
                  e.preventDefault();
                  setError("");
                  setMeetingPreview(true);
                }}
              >
                <label>Meeting title</label>
                <input
                  name="title"
                  value={meeting.title}
                  onChange={updateMeeting}
                  placeholder="e.g. Project discussion"
                  required
                  maxLength={200}
                />
                <label>Date</label>
                <input
                  type="date"
                  name="date"
                  min={new Date().toLocaleDateString("en-CA")}
                  value={meeting.date}
                  onChange={updateMeeting}
                  required
                />
                <label>Start time</label>
                <input
                  type="time"
                  name="start_time"
                  value={meeting.start_time}
                  onChange={updateMeeting}
                  required
                />
                <label>Duration</label>
                <select
                  name="duration_minutes"
                  value={meeting.duration_minutes}
                  onChange={updateMeeting}
                >
                  <option value="15">15 minutes</option>
                  <option value="30">30 minutes</option>
                  <option value="45">45 minutes</option>
                  <option value="60">1 hour</option>
                  <option value="90">1 hour 30 minutes</option>
                  <option value="120">2 hours</option>
                  <option value="180">3 hours</option>
                </select>
                <label>Description</label>
                <textarea
                  name="description"
                  value={meeting.description}
                  onChange={updateMeeting}
                  placeholder="Meeting agenda or additional details"
                  rows="3"
                />
                <button type="submit">Review Meeting</button>
                <button
                  type="button"
                  onClick={() => { setShowMeetingForm(false); setMeeting(emptyMeeting); setMeetingPreview(false); setCommand(""); }}
                >
                  Cancel
                </button>
              </form>
            ) : (
              <div className="email-draft">
                <h3>Review your meeting</h3>
                <div className="draft-field">
                  <strong>Title</strong>
                  <p>{meeting.title}</p>
                </div>
                <div className="draft-field">
                  <strong>Date</strong>
                  <p>{meeting.date}</p>
                </div>
                <div className="draft-field">
                  <strong>Time</strong>
                  <p>{meeting.start_time}</p>
                </div>
                <div className="draft-field">
                  <strong>Duration</strong>
                  <p>{meeting.duration_minutes} minutes</p>
                </div>
                <div className="draft-field">
                  <strong>Description</strong>
                  <p>{meeting.description || "No description"}</p>
                </div>
                <button
                  type="button"
                  disabled={loading}
                  onClick={confirmMeeting}
                >
                  {loading ? "Adding..." : "Confirm & Add to Calendar"}
                </button>
                <button
                  type="button"
                  disabled={loading}
                  onClick={() => setMeetingPreview(false)}
                >
                  Edit Meeting
                </button>
              </div>
            )}
          </section>
        )}
        {loading && (
          <section className="result-card" role="status">
            <div className="loader" />
            <div>
              <strong>AgentOS is working...</strong>
              <p>Processing your request.</p>
            </div>
          </section>
        )}
        {error && (
          <section className="result-card error">
            <strong>Unable to complete request</strong>
            <p>{error}</p>
          </section>
        )}
        {!showMeetingForm && (
        <section className="result-card calendar-section">
          <div className="result-heading">
            <div>
              <span className="eyebrow">GOOGLE CALENDAR</span>
              <h2>Calendar Management</h2>
              <p>View and manage your upcoming meetings.</p>
            </div>
            <button
              type="button"
              className="calendar-refresh"
              onClick={loadCalendarEvents}
              disabled={calendarLoading}
            >
              ↻ Refresh
            </button>
          </div>
          {calendarLoading && (
            <p className="calendar-info">Loading your calendar...</p>
          )}
          {calendarError && (
            <div className="calendar-error">
              <strong>Calendar operation failed</strong>
              <p>{calendarError}</p>
            </div>
          )}
          {!calendarLoading && !calendarError && calendarEvents.length === 0 && (
            <p className="calendar-info">
              No upcoming meetings found. Your calendar is clear.
            </p>
          )}
          <div className="calendar-list">
            {calendarEvents.map((event, index) => (
              <article className="calendar-event" key={event.id || index}>
                <div className="calendar-event-details">
                  <span className="event-mark">●</span>
                  <div>
                    <strong>{event.title || "Untitled meeting"}</strong>
                    <p>{formatDate(event.start)}</p>
                    {event.end && (
                      <p className="event-end">
                        Ends: {formatDate(event.end)}
                      </p>
                    )}
                    {event.description && (
                      <p className="event-description">
                        {event.description}
                      </p>
                    )}
                  </div>
                </div>
                <div className="calendar-actions">
                  <button
                    type="button"
                    className="edit-button"
                    onClick={() => openEditForm(event)}
                  >
                    Edit
                  </button>
                  <button
                    type="button"
                    className="delete-button"
                    onClick={() => deleteMeeting(event)}
                  >
                    Delete
                  </button>
                </div>
              </article>
            ))}
          </div>
          {editingEvent && (
            <div className="edit-panel">
              <div className="result-heading">
                <div>
                  <span className="eyebrow">EDIT EVENT</span>
                  <h2>Update Meeting</h2>
                </div>
                <button
                  type="button"
                  className="calendar-refresh"
                  onClick={() => setEditingEvent(null)}
                  disabled={editLoading}
                >
                  Close
                </button>
              </div>
              <form className="meeting-form" onSubmit={saveEditedMeeting}>
                <label>Meeting title</label>
                <input
                  name="title"
                  value={editMeeting.title}
                  onChange={updateEditMeeting}
                  required
                  maxLength={200}
                />
                <label>Date</label>
                <input
                  type="date"
                  name="date"
                  value={editMeeting.date}
                  onChange={updateEditMeeting}
                  required
                />
                <label>Start time</label>
                <input
                  type="time"
                  name="start_time"
                  value={editMeeting.start_time}
                  onChange={updateEditMeeting}
                  required
                />
                <label>Duration</label>
                <select
                  name="duration_minutes"
                  value={editMeeting.duration_minutes}
                  onChange={updateEditMeeting}
                >
                  <option value="15">15 minutes</option>
                  <option value="30">30 minutes</option>
                  <option value="45">45 minutes</option>
                  <option value="60">1 hour</option>
                  <option value="90">1 hour 30 minutes</option>
                  <option value="120">2 hours</option>
                  <option value="180">3 hours</option>
                  <option value="240">4 hours</option>
                  <option value="480">8 hours</option>
                </select>
                <label>Description</label>
                <textarea
                  name="description"
                  value={editMeeting.description}
                  onChange={updateEditMeeting}
                  rows="3"
                />
                <button type="submit" disabled={editLoading}>
                  {editLoading ? "Updating..." : "Save Changes"}
                </button>
                <button
                  type="button"
                  disabled={editLoading}
                  onClick={() => setEditingEvent(null)}
                >
                  Cancel
                </button>
              </form>
            </div>
          )}
        </section>
        )}
        {result && !showMeetingForm && (
          <section className="result-card">
            <div className="result-heading">
              <div>
                <span className="eyebrow">RESULT</span>
                <h2>{result.agent || "AgentOS"}</h2>
              </div>
              <span className="result-badge">Completed</span>
            </div>
            <p>{result.message || "Your request has been processed."}</p>
            {result.draft && (
              <div className="email-draft">
                <h3>Email draft</h3>
                <div className="draft-field">
                  <strong>To</strong>
                  <p>{result.draft.recipient || "Not specified"}</p>
                </div>
                <div className="draft-field">
                  <strong>Subject</strong>
                  <p>{result.draft.subject}</p>
                </div>
                <div className="draft-field">
                  <strong>Message</strong>
                  <p className="draft-body">{result.draft.body}</p>
                </div>
                <button type="button" onClick={copyDraft}>
                  Copy Draft
                </button>
                {copyMessage && <p>{copyMessage}</p>}
                <p className="draft-safety">
                  This is a draft only. No email has been sent.
                </p>
              </div>
            )}
            {result.events?.length > 0 && (
              <div className="events">
                <h3>Upcoming events</h3>
                {result.events.map((event, i) => (
                  <article className="event" key={event.id || i}>
                    <span className="event-mark">•</span>
                    <div>
                      <strong>{event.title}</strong>
                      <p>{formatDate(event.start)}</p>
                    </div>
                  </article>
                ))}
              </div>
            )}
            {result.intent === "calendar" && result.events?.length === 0 && (
              <p>No upcoming calendar events were found.</p>
            )}
            {result.results?.length > 0 && (
              <div className="events">
                <h3>Search results</h3>
                {result.results.map((item, i) => (
                  <article className="event" key={i}>
                    <div>
                      <strong>
                        {typeof item === "string"
                          ? item
                          : item.file || item.task || "Result"}
                      </strong>
                      {item.message && <p>{item.message}</p>}
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
        )}
        <footer>AgentOS · Multi-agent workflow assistant</footer>
      </main>
    </div>
  );
}