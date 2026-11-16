def detect_intent(command):
    command = " ".join(command.lower().strip().split())

    if not command:
        return "empty"

    email_words = [
        "draft email", "write email", "compose email",
        "create email", "draft an email", "write an email",
        "compose an email", "send an email", "email to"
    ]

    if any(word in command for word in email_words):
        return "communication"

    calendar_words = [
        "meeting", "meetings", "calendar", "schedule",
        "appointment", "appointments", "events", "event",
        "agenda", "upcoming", "my plans"
    ]

    if any(word in command for word in calendar_words):
        return "calendar"

    return "unknown"
