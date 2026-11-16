import unittest
from unittest.mock import patch
from intelligence.intent_engine import detect_intent
from agents.communication import CommunicationAgent
from agents.supervisor import SupervisorAgent
class TestIntentEngine(unittest.TestCase):
    def test_empty_command(self):
        self.assertEqual(detect_intent("   "), "empty")
    def test_calendar_command(self):
        self.assertEqual(detect_intent("Show my upcoming meetings"), "calendar")
    def test_email_command(self):
        self.assertEqual(detect_intent("Draft an email to Alex"), "communication")
    def test_unknown_command(self):
        self.assertEqual(detect_intent("Tell me a joke"), "unknown")
class TestCommunicationAgent(unittest.TestCase):
    def setUp(self):
        self.agent = CommunicationAgent()
    def test_valid_email_recipient(self):
        result = self.agent.process(
            "Draft email to alex@example.com | subject: Update | message: Project is progressing."
        )
        self.assertTrue(result["draft"]["recipient_valid"])
    def test_invalid_email_recipient(self):
        result = self.agent.process(
            "Draft email to Alex | subject: Update | message: Hello."
        )
        self.assertFalse(result["draft"]["recipient_valid"])
    def test_email_is_never_sent(self):
        result = self.agent.process(
            "Draft email to alex@example.com | subject: Update | message: Hello."
        )
        self.assertEqual(result["status"], "draft_only")
        self.assertFalse(result["sent"])
    def test_empty_email_command(self):
        result = self.agent.process("")
        self.assertEqual(result["status"], "needs_input")
        self.assertIsNone(result["draft"])
class TestSupervisor(unittest.TestCase):
    def setUp(self):
        self.supervisor = SupervisorAgent()
    def test_routes_email_to_communication_agent(self):
        result = self.supervisor.process(
            "Draft email to alex@example.com | subject: Update | message: Hello."
        )
        self.assertEqual(result["agent"], "Communication")
        self.assertFalse(result["sent"])
    @patch("agents.supervisor.get_calendar_events")
    def test_routes_calendar_command(self, mock_events):
        mock_events.return_value = [
            {"title": "Team Meeting", "start": "2026-11-01T10:00:00"}
        ]
        result = self.supervisor.process("Show my upcoming meetings")
        self.assertEqual(result["agent"], "Scheduler")
        self.assertEqual(len(result["events"]), 1)
        mock_events.assert_called_once()
if __name__ == "__main__":
    unittest.main(verbosity=2)