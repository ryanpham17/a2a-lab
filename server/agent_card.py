from typing import Any


AGENT_CARD = {
    "id": "echo-agent-v1",
    "name": "Echo Agent",
    "version": "1.0.0",
    "description": "A simple agent that echoes back any text it receives.",
    "url": "https://echo-a2a-agent-kfh6ytqifq-uc.a.run.app/",
    "capabilities": {
        "streaming": False,
        "pushNotifications": False
    },
    "defaultInputModes": ["text/plain"],
    "defaultOutputModes": ["text/plain"],
    "skills": [
        {
            "id": "echo",
            "name": "Echo",
            "description": "Returns the user message verbatim.",
            "inputModes": ["text/plain"],
            "outputModes": ["text/plain"]
        },
        {
            "id": "summarise",
            "name": "Summarise",
            "description": "Returns a short one-sentence summary of the input.",
            "inputModes": ["text/plain"],
            "outputModes": ["text/plain"]
        }
    ],
    "contact": {
        "email": "ryandpham@cpp.edu"
    }
}


def validate_card(card: dict[str, Any]) -> bool:
    """
    Validate that the Agent Card contains all required top-level fields.
    Returns True if valid, otherwise False.
    """
    required_fields = [
        "id",
        "name",
        "version",
        "description",
        "url",
        "capabilities",
        "defaultInputModes",
        "defaultOutputModes",
        "skills",
        "contact",
    ]

    for field in required_fields:
        if field not in card:
            return False

    if "email" not in card["contact"]:
        return False

    return True