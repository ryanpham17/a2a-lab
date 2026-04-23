from client import A2AClient


def main():
    with A2AClient("https://echo-a2a-agent-kfh6ytqifq-uc.a.run.app") as client:
        card = client.fetch_agent_card()
        print("Agent name:", card.get("name"))

        skills = client.get_skills()
        print("Skills:")
        for skill in skills:
            print(f" - {skill['name']} ({skill['id']})")

        response = client.send_task("Hello from the client!")
        result = client.extract_text(response)
        print("Agent response:", result)


if __name__ == "__main__":
    main()