from vertexai.preview import reasoning_engines
import vertexai

vertexai.init(project="a2a-lab-rdpham", location="us-central1")

ENGINE_ID = "2934860967080624128"

agent = reasoning_engines.ReasoningEngine(
    f"projects/189315176867/locations/us-central1/reasoningEngines/{ENGINE_ID}"
)

response = agent.query(message_text="Hello from Agent Engine!")
print(response)