# 🤖 Autonomous ReAct AI Agentic System

A robust, stream-lit powered AI Agentic System capable of multi-step reasoning, dynamic tool selection, and fallback model orchestration using the Groq API.

## 🏗️ System Architecture

```text
  ┌──────────────┐     ┌───────────────────────┐     ┌────────────────────────┐
  │  User Input  │ ──> │ Dynamic Model Router  │ ──> │ ReAct Agent Loop       │
  └──────────────┘     └───────────────────────┘     └───────────┬────────────┘
                                                                 │
                                                                 ▼
  ┌──────────────┐     ┌───────────────────────┐     ┌────────────────────────┐
  │ Final Output │ <── │  Streamlit Dashboard  │ <── │ Tool Execution Engine  │
  └──────────────┘     └───────────────────────┘     │ - web_search           │
                                                     │ - calculate            │
                                                     │ - exec_python          │
                                                     │ - save_to_file         │
                                                     └────────────────────────┘