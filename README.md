# AI Agent Webhook Platform

A lightweight, extensible AI agent backend built with FastAPI that combines LLM-driven chat with dynamic tool execution, persistent context, and analytics.

This project acts as a bridge between natural language input and real backend actions (API calls, database operations, email sending), with a modular tool system that can be extended at runtime.

The frontend dashboard (see `index.html`) provides a minimal interface for interacting with the agent, inspecting tool usage, and testing integrations.

---

## Description

This system implements an AI agent that:

* Parses user intent from natural language
* Maintains session-based memory
* Dynamically selects and executes external tools
* Tracks execution analytics (latency, success rate)
* Supports real actions like saving users, querying data, and sending emails

The core orchestration logic lives in [`services/agent_service.py`](./services/agent_service.py) and acts as the runtime for:

* intent detection
* context extraction
* tool routing
* LLM fallback

---

## Interesting Techniques

### Intent-driven routing (hybrid AI + rules)

The system combines:

* Rule-based intent detection in [`utils/intent.py`](./utils/intent.py)
* LLM fallback via Groq API

This reduces unnecessary LLM calls for deterministic operations.

---

### Context extraction via regex pipelines

User identity is extracted incrementally using regex patterns:

* Email parsing + normalization
* Name extraction with guarded patterns
* Context merging strategy

Relevant file: [`services/agent_service.py`](./services/agent_service.py)

MDN reference:
[https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Regular_expressions](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Regular_expressions)

---

### Async tool execution with retry logic

External tools are executed using:

* `httpx.AsyncClient`
* Retry loop with delay
* JSON fallback parsing

Key pattern:

* Non-blocking IO using Python async/await

MDN reference:
[https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function)

---

### Schema-driven tool validation

Each tool defines:

* `input_schema`
* `output_schema`

Runtime validation checks required fields before execution.

---

### MongoDB-backed analytics aggregation

Tool usage is tracked and summarized using:

* aggregation pipelines (`$group`, `$avg`, `$max`)
* latency measurement in ms
* success rate calculation

Relevant file: [`routes/tools.py`](./routes/tools.py)

---

### Session-based in-memory state management

State is maintained using:

* `chat_memory`
* `user_context`
* `user_state`

Supports:

* multi-step flows
* pending actions (e.g., confirmations)

---

### Dynamic tool registry (runtime extensibility)

Tools are:

* stored in MongoDB (`tools_collection`)
* added via API (`POST /tools`)
* executed dynamically

---

### Frontend: minimal reactive dashboard (no framework)

The UI in `index.html` uses:

* Fetch API
* DOM manipulation via `document.createElement`

MDN references:

* [https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)
* [https://developer.mozilla.org/en-US/docs/Web/API/Document/createElement](https://developer.mozilla.org/en-US/docs/Web/API/Document/createElement)

---

## Technologies & Libraries

* FastAPI
* Groq (LLM inference)
* httpx (async HTTP client)
* pymongo (MongoDB driver)
* python-dotenv (environment config)
* pydantic (data validation)

Native:

* smtplib (email)
* asyncio (concurrency)

---

## Project Structure

```bash
.
├── core/
├── models/
├── routes/
├── services/
├── utils/
├── prompts/
├── .venv/
├── .vscode/
├── __pycache__/
├── main.py
├── index.html
├── requirements.txt
├── .env
```

### Directory notes

* `core/`
  Configuration and database initialization
  → see [`core/config.py`](./core/config.py), [`core/database.py`](./core/database.py)

* `models/`
  Pydantic schemas for request validation

* `routes/`
  API surface (FastAPI routers)

* `services/`
  Core business logic

* `utils/`
  Stateless helpers + in-memory state

* `prompts/`
  System prompt configuration

* `index.html`
  Minimal dashboard UI

---

## Notable Files

* [`main.py`](./main.py)
  Application entrypoint

* [`services/agent_service.py`](./services/agent_service.py)
  Core orchestration engine

* [`services/tool_executor.py`](./services/tool_executor.py)
  Async execution + analytics

* [`routes/tools.py`](./routes/tools.py)
  Tool registry + analytics endpoints

* [`routes/data.py`](./routes/data.py)
  User persistence + validation

---

## Design Notes

* Clear separation between intent, execution, and persistence
* Minimal abstractions
* Emphasis on debuggability and extensibility

---

## Limitations (v1)

* In-memory session state (not distributed)
* No authentication layer
* Basic schema validation
* Email limited to Gmail SMTP
