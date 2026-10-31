from intent_engine import IntentEngine


engine = IntentEngine()

requests = [
    "Schedule a meeting tomorrow",
    "Send a message to my team",
    "Find the latest project report",
    "Find the project report and send it to my team"
]

for request in requests:

    result = engine.analyze(request)

    print()
    print("Request:", request)
    print("Intents:", result)