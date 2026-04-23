# A2A Protocol Assignment — Report

**Name:** Ryan Pham
**Course:** CS4680

---

## Section 3 — Request & Response Schema Analysis

### Q1: Why does the request use a client-generated `id` rather than a server-generated one? What problem does this solve in distributed systems?

Using a client-generated `id` solves the problem of **idempotency in unreliable networks**. In a distributed system, a client may send a request and then lose the network connection before receiving a response. Without a client-generated ID, the client has no way to know whether the server received and processed the request — so retrying would risk executing the task twice.

With a client-generated UUID, the client can safely resend the same task with the same `id`. A well-implemented server can detect that it has already processed a task with that ID and return the cached result rather than executing the task again. This makes operations idempotent, which is critical for reliability in distributed environments where partial failures are common.

It also decouples task tracking from server state: the client can reference, log, and correlate a task before the server even receives it.

---

### Q2: The `status.state` can be `'working'`. Under what circumstances would a server return this state in a non-streaming call, and how should a client react?

In a non-streaming call, a server would return `status.state: "working"` when the task has been accepted and queued but has not yet completed by the time the HTTP response is sent. This typically happens when the agent offloads work to a background job queue, a separate worker process, or a long-running model inference pipeline that cannot complete within a single synchronous HTTP response cycle.

A client that receives `"working"` should implement a **polling loop**: it should wait a short interval (e.g. 1–2 seconds) and then re-query the server for the task status using the original client-generated task `id`. The client should continue polling until the state transitions to `"completed"`, `"failed"`, or `"canceled"`, and should implement a timeout and backoff strategy to avoid hammering the server indefinitely.

---

### Q3: What is the purpose of the `sessionId` field? Give a concrete example of two related tasks that should share a session.

The `sessionId` field groups multiple tasks into a single logical conversation or workflow. It allows the server to maintain context across requests — for example, storing conversation history, user preferences, or intermediate results that should persist between calls within the same session.

**Concrete example:** A user interacts with a research agent in two steps:

1. **Task 1** — The user sends: *"Summarise the key points of the A2A protocol."* The agent returns a summary. This task is assigned `sessionId: "session-abc-123"`.
2. **Task 2** — The user follows up: *"Now give me three exam questions based on that summary."* This second task also carries `sessionId: "session-abc-123"`.

Without the shared `sessionId`, the server would have no way to associate the follow-up request with the earlier summary. With it, the server can retrieve the context from Task 1 and generate relevant exam questions rather than asking the user to repeat themselves.

---

### Q4: The `parts` array supports types `text`, `file`, and `data`. Describe a realistic multi-agent workflow where all three part types appear in a single conversation.

Consider a **document analysis pipeline** with three specialised agents:

1. **User → Ingestion Agent** — The user sends a task with a `file` part (e.g. a PDF contract uploaded to cloud storage) and a `text` part containing the instruction: *"Extract all payment clauses from this contract."* The file part carries the GCS URL and MIME type; the text part carries the natural language instruction.

2. **Ingestion Agent → Analysis Agent** — The ingestion agent extracts structured clause data and forwards it to a second agent using a `data` part (a JSON object containing the extracted clauses as key-value pairs) alongside a `text` part: *"Classify each clause by risk level."*

3. **Analysis Agent → User** — The analysis agent returns its findings as a `text` part (a human-readable risk summary) and a `file` part (a downloadable PDF report generated from the analysis).

This workflow uses all three part types naturally: `file` for binary content transfer, `data` for structured inter-agent communication, and `text` for human-readable instructions and responses.

---

## Section 4 — Cloud Run Deployment

### (a) What does `--allow-unauthenticated` do and what are its security implications?

The `--allow-unauthenticated` flag configures the Cloud Run service to accept HTTP requests from **any caller without requiring a Google identity token**. By default, Cloud Run services require callers to present a valid Google-signed bearer token in the `Authorization` header, which restricts access to authenticated Google Cloud identities (service accounts, users, etc.).

**Security implications:**

- **Public exposure:** The service becomes reachable by anyone on the internet, including malicious actors. Any endpoint — including `/tasks/send` — can be called without credentials.
- **No access control:** Without authentication, there is no built-in way to restrict which clients can submit tasks or how many they can submit.
- **Rate limiting and abuse:** An unauthenticated public endpoint is vulnerable to denial-of-service attacks and abuse. For a production A2A agent, you would want to add API key validation, OAuth2, or restrict the flag and use IAM-based invocation instead.
- **Acceptable for labs:** For this assignment, `--allow-unauthenticated` is appropriate because it allows the A2A client and `demo.py` to reach the service without credential management overhead. In production, this flag should be removed and callers should authenticate with service account tokens.

---

### (b) How does Cloud Run scale to zero, and what does cold start latency mean for A2A clients?

Cloud Run automatically scales the number of container instances up and down based on incoming request traffic. When there are no requests for a configurable idle period (default: a few minutes), Cloud Run **scales to zero** — all instances are shut down and no compute resources are consumed or billed.

When a new request arrives after the service has scaled to zero, Cloud Run must start a fresh container instance before the request can be handled. This startup time is called the **cold start latency**. For a Python FastAPI service like our Echo Agent, cold start typically adds 1–3 seconds of overhead on the first request.

**Implications for A2A clients:**

- The client's `httpx.Client` has a `timeout=30` seconds configured, which is long enough to absorb a cold start. However, if the timeout were too short, the first request after a period of inactivity would fail with a timeout error.
- For production A2A agents, you can mitigate cold starts by setting a minimum instance count of 1 (`--min-instances=1`), which keeps at least one warm instance running at all times at a small additional cost.
- A2A clients should be designed to handle slow first responses gracefully — either with a generous timeout or a retry mechanism.

---

## Section 5 — Vertex AI Agent Engine Deployment

### (a) Cloud Run vs Agent Engine: operational burden and use-case fit

| | **Cloud Run** | **Agent Engine** |
|---|---|---|
| **Deployment unit** | Docker container | Python class (pickled) |
| **Infrastructure** | You manage the Dockerfile, base image, and dependencies | Google manages the runtime entirely |
| **Operational burden** | Medium — you own the container build, port binding, health checks | Low — no container to write or maintain |
| **Observability** | Cloud Logging + custom instrumentation | Built-in agent tracing and logging via Vertex AI |
| **Use-case fit** | General-purpose HTTP services; any language or framework | Python-based AI agents; LangGraph, LangChain, A2A |
| **Scaling** | Scales to zero; configurable concurrency | Managed automatically by Vertex AI |
| **Best for** | Agents that need custom HTTP endpoints, streaming, or non-Python runtimes | Agents that are purely Python and benefit from Vertex AI's managed lifecycle |

**Summary:** Cloud Run is the better choice when you need full control over the HTTP interface, want to support the full A2A protocol including streaming, or need to deploy non-Python agents. Agent Engine is better when you want to minimise operational overhead and keep the agent fully within the Google Cloud AI ecosystem, trading flexibility for simplicity.

---

### (b) Why does the wrapper use a synchronous `query()` method even though the underlying handler is async?

The Agent Engine runtime calls `query()` from its own internal execution environment, which already runs an event loop. Python's `asyncio.run()` cannot be called from within a running event loop — doing so raises a `RuntimeError`. Since Agent Engine controls the execution context and does not expose a way to `await` coroutines from the wrapper class, `query()` must be synchronous.

The solution used in this project is to make `handle_task` a plain synchronous function, removing the `async` keyword entirely. This is valid because `handle_task` performs no I/O — it only manipulates strings in memory. There is no actual benefit to making it a coroutine, and removing `async` eliminates the need for any event loop management in the wrapper. For handlers that genuinely require async I/O (e.g. calling an external API), the correct approach is to run the coroutine in a separate thread with its own event loop using `concurrent.futures.ThreadPoolExecutor`.

---

## Section 6 — Client-Server Connection Trace

### Log Output from `demo.py` (against Cloud Run)

```
[CLIENT] GET https://echo-a2a-agent-kfh6ytqifq-uc.a.run.app/.well-known/agent.json
[CLIENT] Response 200: {"id":"echo-agent-v1","name":"Echo Agent","version":"1.0.0","description":"A simple agent that echoes back any text it receives.","url":"https://echo-a2a-agent-kfh6ytqifq-uc.a.run.app/","capabilities"
Agent name: Echo Agent
Skills:
 - Echo (echo)
 - Summarise (summarise)
[CLIENT] POST https://echo-a2a-agent-kfh6ytqifq-uc.a.run.app/tasks/send
[CLIENT] Payload: {'id': '77eec747-eb2e-4c9b-ba22-ee69bfd67515', 'sessionId': None, 'message': {'role': 'user', 'parts': [{'type': 'text', 'text': 'Hello from the client!'}]}}
[CLIENT] Response 200: {"id":"77eec747-eb2e-4c9b-ba22-ee69bfd67515","status":{"state":"completed","message":null},"artifacts":[{"index":0,"name":"result","parts":[{"type":"text","text":"Hello from the client!"}]}]}
Agent response: Hello from the client!
```

---

### UML Sequence Diagram

```
User          A2AClient            Cloud Run (A2AServer)       handlers.py
 |                |                          |                       |
 | demo.py        |                          |                       |
 |--------------->|                          |                       |
 |                |  GET /.well-known/       |                       |
 |                |    agent.json            |                       |
 |                |------------------------->|                       |
 |                |                          |                       |
 |                |  200 OK (Agent Card)     |                       |
 |                |<-------------------------|                       |
 |                |                          |                       |
 | send_task()    |                          |                       |
 |--------------->|                          |                       |
 |                |  POST /tasks/send        |                       |
 |                |  {id, message, parts}    |                       |
 |                |------------------------->|                       |
 |                |                          |  handle_task(request) |
 |                |                          |---------------------->|
 |                |                          |                       |
 |                |                          |  return result_text   |
 |                |                          |<----------------------|
 |                |                          |                       |
 |                |  200 OK                  |                       |
 |                |  {id, status, artifacts} |                       |
 |                |<-------------------------|                       |
 |                |                          |                       |
 | print response |                          |                       |
 |<---------------|                          |                       |
```

---

### Retry Safety and Idempotency

**If a client loses the network connection after sending the POST but before receiving the response, how could it safely retry?**

The client should catch the network exception (e.g. `httpx.ReadTimeout` or `httpx.NetworkError`) and resend the exact same request — using the **same task `id`** that was generated before the first attempt. A correctly implemented A2A server can detect the duplicate `id` and return the result of the already-completed task without re-executing the handler logic.

The retry loop should use **exponential backoff** (e.g. wait 1s, then 2s, then 4s) to avoid overwhelming a server that may be recovering from a transient failure, and should cap the number of retries (e.g. 3–5 attempts) before surfacing an error to the user.

**What field in the A2A protocol helps with idempotency?**

The **`id` field** in the task request object is the idempotency key. Because it is client-generated (a UUID created before the first send attempt), the client can reuse it across retries. The server uses this ID to deduplicate requests — if a task with a given `id` has already been completed, the server returns the cached response instead of processing the task again. This guarantees that even if the network fails mid-flight, retrying with the same `id` will never cause the task to be executed more than once.