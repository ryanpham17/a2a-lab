# A2A Lab — Agent-to-Agent Protocol with Python

A minimal but fully functional Agent-to-Agent (A2A) system built with FastAPI, deployed to Google Cloud Run and Vertex AI Agent Engine.

---

## Live Deployment

| Service | URL |
|---|---|
| Cloud Run | https://echo-a2a-agent-kfh6ytqifq-uc.a.run.app |
| Agent Card | https://echo-a2a-agent-kfh6ytqifq-uc.a.run.app/.well-known/agent.json |

---

## Project Structure

```
a2a-lab/
  server/
    main.py                # A2A Server (FastAPI)
    agent_card.py          # Agent Card definition
    handlers.py            # Task handler logic
    agent_engine_wrapper.py  # Vertex AI Agent Engine wrapper
    Dockerfile
    requirements.txt
  client/
    client.py              # A2A Client
    demo.py                # End-to-end demo script
  cloud/
    deploy_cloud_run.sh    # Cloud Run deployment script
    deploy_agent_engine.py # Agent Engine deployment script
  report.md
  README.md
```

---

## Environment Setup

### Prerequisites

- Python 3.10 or newer
- Docker Desktop
- Google Cloud CLI (`gcloud`)
- A Google Cloud project with billing enabled
- APIs enabled: Cloud Run, Artifact Registry, Vertex AI

### Install Dependencies

```bash
# Create and activate virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate

# Install packages
pip install fastapi uvicorn httpx pydantic google-cloud-aiplatform google-auth requests cloudpickle
```

---

## Part 1 — Run the Server Locally

```bash
uvicorn server.main:app --reload --port 8000
```

Test the endpoints:

```bash
# Health check
curl http://localhost:8000/health

# Agent Card
curl http://localhost:8000/.well-known/agent.json

# Send an echo task
curl -X POST http://localhost:8000/tasks/send \
  -H "Content-Type: application/json" \
  -d '{"id":"t1","message":{"role":"user","parts":[{"type":"text","text":"Hello A2A"}]}}'

# Send a summarise task
curl -X POST http://localhost:8000/tasks/send \
  -H "Content-Type: application/json" \
  -d '{"id":"t2","message":{"role":"user","parts":[{"type":"text","text":"!summarise This is a long document about cats"}]}}'
```

---

## Part 2 — Run the Client Demo

Make sure the server is running locally or point `demo.py` at the Cloud Run URL, then:

```bash
python client/demo.py
```

Expected output:
```
Agent name: Echo Agent
Skills:
 - Echo (echo)
 - Summarise (summarise)
Agent response: Hello from the client!
```

---

## Part 3 — Deploy to Cloud Run

```bash
bash cloud/deploy_cloud_run.sh
```

This will:
1. Create an Artifact Registry repository
2. Build and push the Docker image
3. Deploy to Cloud Run
4. Print the live service URL

---

## Part 4 — Deploy to Vertex AI Agent Engine

```bash
python cloud/deploy_agent_engine.py
```

This will:
1. Package the `EchoAgent` class
2. Upload to GCS staging bucket
3. Deploy to Vertex AI Agent Engine
4. Print the Engine ID

To test the deployed agent:

```bash
python cloud/test_agent_engine.py
```

---

## Agent Skills

| Skill | Trigger | Behaviour |
|---|---|---|
| Echo | Any text | Returns the input unchanged |
| Summarise | Text starting with `!summarise` | Returns a one-sentence mock summary |