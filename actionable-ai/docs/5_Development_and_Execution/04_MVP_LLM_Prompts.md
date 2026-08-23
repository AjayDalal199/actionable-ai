# 04 MVP LLM Prompts & Agent Schemas

## Document Metadata
- **Status:** Approved
- **Scope:** Strictly MVP (Phase 1)
- **Last Updated:** 2026-08-23

---

## 1. Core System Prompt

This is the baseline instruction fed into the LangGraph orchestrator. It ensures the AI behaves professionally and strictly adheres to its registered tools.

```text
You are an Enterprise AI Assistant designed to help internal employees execute complex API workflows and retrieve internal knowledge.

You have access to a set of internal tools. 
If the user asks a question, retrieve the answer from your vector knowledge base.
If the user asks you to perform an action, you must find the appropriate tool and invoke it.

CRITICAL SECURITY RULE:
If a tool requires Human-in-the-Loop (HITL) confirmation, you MUST NOT attempt to execute the tool directly. Instead, you must invoke the `request_hitl_approval` function, providing the exact action name and the parsed parameters. 
You will be suspended (paused) until the human explicitly grants approval. Under no circumstances can you bypass this approval for destructive actions (DELETE, POST, PUT).
```

---

## 2. Tool Calling Schemas (Pydantic / OpenAI Functions)

When we pass the registered tools from the Database to the LLM, we dynamically convert the JSON schemas into Pydantic models. 

### 2.1. The HITL Interceptor Schema
To enforce our "Action Required" UI cards, we inject this specific schema into every LLM request. This teaches the LLM *how* to ask for permission.

```json
{
  "name": "request_hitl_approval",
  "description": "Call this tool whenever you need to execute an action that is flagged as 'requires_hitl: true'. This will pause your execution and trigger a warning card on the user's screen.",
  "parameters": {
    "type": "object",
    "properties": {
      "tool_name": {
        "type": "string",
        "description": "The exact name of the registered tool you want to run."
      },
      "tool_arguments": {
        "type": "object",
        "description": "The JSON object containing the parsed arguments for the tool."
      },
      "human_readable_summary": {
        "type": "string",
        "description": "A 1-sentence summary explaining to the user exactly what this action will do, so they can make an informed decision to approve or reject."
      }
    },
    "required": ["tool_name", "tool_arguments", "human_readable_summary"]
  }
}
```

### 3. Orchestration Logic (LangGraph)
When the LLM outputs a function call for `request_hitl_approval`, the LangGraph node graph hits a conditional edge (`END` or `PAUSE`). 
The FastAPI backend intercepts this, generates a `pending_action_id`, stores the state in Redis, and emits the Server-Sent Event to the Widget to render the Red/Green Confirmation card.
