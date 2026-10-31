class SupervisorAgent:

    def process(self, request):

        request = request.lower()

        if "meeting" in request or "schedule" in request:
            return {
                "agent": "scheduler",
                "task": request
            }

        if "message" in request or "send" in request:
            return {
                "agent": "communication",
                "task": request
            }

        if "file" in request or "document" in request:
            return {
                "agent": "file_data",
                "task": request
            }

        return {
            "agent": "unknown",
            "task": request
        }