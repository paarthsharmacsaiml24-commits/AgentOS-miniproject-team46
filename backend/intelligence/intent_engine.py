class IntentEngine:

    def analyze(self, request):

        request = request.lower()

        intents = []

        scheduling_words = [
            "schedule",
            "meeting",
            "calendar",
            "appointment",
            "book",
            "reschedule"
        ]

        communication_words = [
            "send",
            "message",
            "email",
            "notify",
            "tell",
            "contact"
        ]

        file_words = [
            "file",
            "document",
            "report",
            "presentation",
            "pdf",
            "folder",
            "find"
        ]

        for word in scheduling_words:
            if word in request:
                intents.append("scheduling")
                break

        for word in communication_words:
            if word in request:
                intents.append("communication")
                break

        for word in file_words:
            if word in request:
                intents.append("file_data")
                break

        if not intents:
            intents.append("unknown")

        return intents
