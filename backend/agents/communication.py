import re
class CommunicationAgent:
    def process(self, command):
        text = command.strip()
        if not text:
            return {
                "status": "needs_input",
                "agent": "Communication",
                "message": "Describe the email you want to draft.",
                "draft": None,
                "sent": False
            }
        recipient_match = re.search(
            r"\bto\s+(.+?)(?=\s+subject:|\s*\|\s*subject:|\s*\|\s*message:|$)",
            text,
            re.IGNORECASE
        )
        subject_match = re.search(
            r"\bsubject:\s*(.+?)(?=\s+message:|\s*\|\s*message:|$)",
            text,
            re.IGNORECASE
        )
        message_match = re.search(
            r"\bmessage:\s*(.+)$",
            text,
            re.IGNORECASE
        )
        recipient = recipient_match.group(1).strip() if recipient_match else ""
        subject = subject_match.group(1).strip() if subject_match else ""
        body = message_match.group(1).strip() if message_match else ""
        if not subject:
            subject = "Follow-up"
        if not body:
            purpose = re.sub(
                r"^(please\s+)?(draft|write|compose|create)\s+(an?\s+)?(email|mail)\s*",
                "",
                text,
                flags=re.IGNORECASE
            ).strip(" .")
            greeting = f"Hi {recipient.split()[0]}," if recipient else "Hello,"
            body = (
                f"{greeting}\n\n"
                "I hope you are doing well.\n\n"
                f"I am reaching out regarding {purpose or 'our recent discussion'}.\n\n"
                "Please let me know your thoughts.\n\n"
                "Best regards"
            )
        email_pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
        recipient_is_email = bool(re.fullmatch(email_pattern, recipient))
        return {
            "status": "draft_only",
            "agent": "Communication",
            "message": (
                "Email draft created. Nothing has been sent."
                if recipient_is_email
                else "Draft created. Add a valid recipient email address before using it."
            ),
            "draft": {
                "recipient": recipient,
                "recipient_valid": recipient_is_email,
                "subject": subject,
                "body": body
            },
            "sent": False
        }