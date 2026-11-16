from typing import TypedDict, Optional
from langgraph.graph import StateGraph, START, END
from intelligence.intent_engine import detect_intent
from intelligence.memory import save_execution
from agents.scheduler import get_calendar_events
from agents.communication import CommunicationAgent
from agents.file_data import file_data_agent
class AgentState(TypedDict):
    command: str
    intent: str
    agent: str
    tasks: list
    results: list
    events: list
    draft: Optional[dict]
    status: str
    message: str
    attempts: int
communication_agent = CommunicationAgent()
MAX_RETRIES = 2
def planner_node(state: AgentState):
    command = state["command"].lower().strip()
    intent = detect_intent(command)
    tasks = []
    if any(word in command for word in [
        "find file", "find files", "search file", "search files",
        "list files", "show files", "search content",
        "search inside"
    ]):
        intent = "file_data"
        tasks = [{
            "type": "file_data",
            "description": "Search or inspect project files",
            "status": "pending",
            "attempts": 0,
            "depends_on": []
        }]
        agent = "File/Data"
    elif intent == "communication":
        tasks = [{
            "type": "email",
            "description": "Create an email draft",
            "status": "pending",
            "attempts": 0,
            "depends_on": []
        }]
        agent = "Communication"
    elif intent == "calendar":
        tasks = [{
            "type": "calendar",
            "description": "Retrieve upcoming calendar events",
            "status": "pending",
            "attempts": 0,
            "depends_on": []
        }]
        agent = "Scheduler"
    elif any(word in command for word in [
        "presentation", "prepare me", "prepare for",
        "plan my week", "organize my day"
    ]):
        intent = "workflow"
        tasks = [
            {
                "type": "calendar",
                "description": "Check upcoming calendar events",
                "status": "pending",
                "attempts": 0,
                "depends_on": []
            },
            {
                "type": "checklist",
                "description": "Create a preparation checklist",
                "status": "pending",
                "attempts": 0,
                "depends_on": ["calendar"]
            }
        ]
        agent = "Multi-Agent Workflow"
    else:
        agent = "Supervisor"
    return {
        "intent": intent,
        "agent": agent,
        "tasks": tasks,
        "results": [],
        "events": [],
        "draft": None,
        "status": "running",
        "attempts": 0
    }
def execute_task(task, command):
    if task["type"] == "calendar":
        return get_calendar_events()
    if task["type"] == "checklist":
        return [
            "Review presentation slides",
            "Practice the presentation",
            "Check presentation equipment",
            "Prepare answers to possible questions"
        ]
    if task["type"] == "email":
        return communication_agent.process(command)
    if task["type"] == "file_data":
        return file_data_agent.process(command)
    raise ValueError(f"Unknown task type: {task['type']}")
def executor_node(state: AgentState):
    tasks = state["tasks"]
    results = []
    events = []
    draft = None
    completed_types = set()
    for task in tasks:
        if not all(
            dependency in completed_types
            for dependency in task["depends_on"]
        ):
            task["status"] = "blocked"
            results.append({
                "task": task["description"],
                "status": "blocked",
                "error": "A dependency was not completed."
            })
            continue
        task["status"] = "running"
        for attempt in range(MAX_RETRIES + 1):
            task["attempts"] = attempt + 1
            try:
                output = execute_task(task, state["command"])

                task["status"] = "completed"
                completed_types.add(task["type"])

                if task["type"] == "calendar":
                    events = output

                if task["type"] == "email":
                    draft = output.get("draft")

                results.append({
                    "task": task["description"],
                    "type": task["type"],
                    "status": "completed",
                    "attempts": task["attempts"],
                    "result": output
                })
                break
            except Exception as error:
                if attempt == MAX_RETRIES:
                    task["status"] = "failed"
                    results.append({
                        "task": task["description"],
                        "type": task["type"],
                        "status": "failed",
                        "attempts": task["attempts"],
                        "error": str(error)
                    })
    return {
        "tasks": tasks,
        "results": results,
        "events": events,
        "draft": draft
    }
def verifier_node(state: AgentState):
    results = state["results"]
    completed = sum(
        1 for result in results
        if result["status"] == "completed"
    )
    failed = sum(
        1 for result in results
        if result["status"] == "failed"
    )
    blocked = sum(
        1 for result in results
        if result["status"] == "blocked"
    )
    if failed or blocked:
        status = "partially_completed" if completed else "failed"
    else:
        status = "completed"
    message = (
        f"Execution finished. {completed} completed, "
        f"{failed} failed, {blocked} blocked."
    )
    save_execution(
        command=state["command"],
        tasks=state["tasks"],
        results=results,
        status=status
    )
    return {
        "status": status,
        "message": message
    }
def unknown_node(state: AgentState):
    return {
        "status": "unsupported",
        "message": (
            "I cannot handle that command yet. "
            "Try asking about your calendar, drafting an email, "
            "finding files, or preparing for a presentation."
        )
    }
def route_after_planning(state: AgentState):
    if not state["tasks"]:
        return "unknown"
    return "executor"
builder = StateGraph(AgentState)
builder.add_node("planner", planner_node)
builder.add_node("executor", executor_node)
builder.add_node("verifier", verifier_node)
builder.add_node("unknown", unknown_node)
builder.add_edge(START, "planner")
builder.add_conditional_edges(
    "planner",
    route_after_planning,
    {
        "executor": "executor",
        "unknown": "unknown"
    }
)
builder.add_edge("executor", "verifier")
builder.add_edge("verifier", END)
builder.add_edge("unknown", END)
agent_graph = builder.compile()
def process_command(command: str):
    initial_state = {
        "command": command,
        "intent": "",
        "agent": "",
        "tasks": [],
        "results": [],
        "events": [],
        "draft": None,
        "status": "pending",
        "message": "",
        "attempts": 0
    }
    return agent_graph.invoke(initial_state)