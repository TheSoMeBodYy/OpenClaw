# OpenClaw – Local Autonomous Agent Prototype

This repository contains an implementation of the “OpenClaw Protocol (Local Agent Edition)” internship task.

The system is a locally running autonomous AI agent built with Streamlit (UI), Ollama (LLM runtime), and ChromaDB (vector memory). The architecture separates UI, agent logic, and memory layers.

## Stack

- Python 3.10+
- Streamlit (UI layer)
- Ollama (local LLM runtime, tested with `gemma:2b`)
- ChromaDB (vector store for long-term memory)
- DuckDuckGo Search (internet tool)

## Functional Coverage

### 1. Configuration & Persona

Sidebar configuration allows runtime modification of:
- User profile (name, info)
- Agent persona (name, role, system instructions)

Changes dynamically influence system prompt construction without resetting the conversation state.

### 2. Memory Architecture

Short-Term Memory:
- Sliding context window
- Raw message history sent to the model

Long-Term Memory (RAG):
- ChromaDB vector storage
- Semantic retrieval before reasoning
- LLM-controlled memory persistence (`save_memory` flag)
- Inspectable in the “Under the Hood” page

### 3. Tools & Reasoning Loop

Available tools:
- Internet search
- Add To-Do task
- Complete To-Do task (fuzzy matching)
- Current date

Reasoning follows a structured JSON loop:

Thought → Action → Observation → Final Answer

Tool execution is performed deterministically, followed by a second-pass model call for response synthesis.

### 4. Proactivity

On startup and after updates, the agent checks for unfinished tasks and proactively suggests follow-up actions.

### 5. Observability

The application includes a dedicated debug page showing:
- Working memory (messages in context)
- Long-term storage (vector entries)
- Internal reasoning log
- Optional relevance scores from vector queries

## How to Run

1. Install dependencies:

   pip install -r requirements.txt

2. Install and run Ollama:

   ollama pull gemma:2b

3. Start the application:

   streamlit run app.py

The system runs fully locally.

## Notes

- JSON parsing includes fallback handling for smaller local model instability.
- Deterministic routing is used for common intents to reduce failure modes.
- The architecture is modular and can be extended with additional tools or memory policies.