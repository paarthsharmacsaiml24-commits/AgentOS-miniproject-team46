from agents.scheduler import get_calendar_events
from agents.communication import CommunicationAgent
from intelligence.intent_engine import detect_intent
class SupervisorAgent:
    def __init__(self):
        self.communication_agent = CommunicationAgent()
    def process(self, command):
        intent = detect_intent(command)
        if intent == "empty":
            return {
                "agent": "Supervisor",
                "intent": "empty",
                "message": "Please enter a command.",
                "events": []
            }
        if intent == "communication":
            return self.communication_agent.process(command)
        if intent == "calendar":
            return {
                "agent": "Scheduler",
                "intent": "calendar",
                "message": "Here are your upcoming calendar events.",
                "events": get_calendar_events()
            }
        return {
            "agent": "Supervisor",
            "intent": "unknown",
            "message": "I cannot handle that command yet. Try asking about your calendar or drafting an email.",
            "events": []
        }