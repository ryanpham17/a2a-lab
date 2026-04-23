import os
import sys

import vertexai
from vertexai.preview import reasoning_engines

PROJECT_ID = "a2a-lab-rdpham"
REGION = "us-central1"
STAGING_BUCKET = f"gs://{PROJECT_ID}-a2a-staging"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from server.agent_engine_wrapper import EchoAgent

vertexai.init(
    project=PROJECT_ID,
    location=REGION,
    staging_bucket=STAGING_BUCKET,
)

remote_agent = reasoning_engines.ReasoningEngine.create(
    EchoAgent(),
    requirements=[
        "fastapi==0.136.0",
        "uvicorn==0.46.0",
        "pydantic==2.13.3",
        "httpx==0.28.1",
        "cloudpickle==3.1.2",
        "google-cloud-aiplatform==1.148.1",
    ],
    extra_packages=[
        "./server",
    ],
    display_name="Echo A2A Agent",
    description="A2A Lab - Echo Agent on Agent Engine",
)

print("Deployed! Resource name:", remote_agent.resource_name)
print("Engine ID:", remote_agent.resource_name.split("/")[-1])