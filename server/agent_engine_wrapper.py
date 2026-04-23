import uuid

try:
    from server.handlers import handle_task
except ModuleNotFoundError:
    from handlers import handle_task


class EchoAgent:
    def set_up(self):
        print("EchoAgent.set_up() called")

    def query(self, *, task_id: str = None, message_text: str) -> dict:
        from types import SimpleNamespace

        fake_request = SimpleNamespace(
            id=task_id or str(uuid.uuid4()),
            message=SimpleNamespace(
                role="user",
                parts=[SimpleNamespace(type="text", text=message_text)]
            )
        )

        result_text = handle_task(fake_request) 

        return {
            "id": fake_request.id,
            "status": {"state": "completed"},
            "artifacts": [
                {
                    "parts": [
                        {"type": "text", "text": result_text}
                    ]
                }
            ]
        }