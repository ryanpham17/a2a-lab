def handle_task(request) -> str:
    text_parts = [p.text for p in request.message.parts if getattr(p, "type", None) == "text"]
    combined = " ".join(text_parts).strip()

    if combined.startswith("!summarise"):
        content = combined[len("!summarise"):].strip()
        if not content:
            return "This is a mock summary: no text was provided to summarise."
        return "This is a mock summary: the text gives a short explanation of the main idea."

    return combined