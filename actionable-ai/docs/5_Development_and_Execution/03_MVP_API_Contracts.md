# 03 MVP API Contracts

## Document Metadata
- **Status:** Approved
- **Scope:** Strictly MVP (Phase 1)
- **Last Updated:** 2026-08-23

---

## 1. Overview
These API contracts define the strict JSON boundaries between the React Dashboard, the Web Component Widget, and the FastAPI Backend. All routes are prefixed with `/api/v1`.

---

## 2. Dashboard Endpoints (Internal)

### 2.1. Upload Knowledge Base Document
*   **Endpoint:** `POST /api/v1/knowledge/upload`
*   **Description:** Accepts a multipart/form-data upload for PDFs or Markdown files.
*   **Request:**
    *   `workspace_id` (UUID - Header or Form Data)
    *   `file` (multipart/form-data, max 50MB)
*   **Response (200 OK):**
```json
{
  "document_id": "uuid-1234",
  "status": "processing",
  "message": "Document uploaded and chunking initiated."
}
```

### 2.2. Register Agent Tool
*   **Endpoint:** `POST /api/v1/tools/register`
*   **Description:** Registers a third-party API endpoint that the LLM is allowed to call.
*   **Request:**
```json
{
  "name": "delete_customer_account",
  "http_method": "DELETE",
  "url": "https://api.internal.corp/customers/{id}",
  "requires_hitl": true,
  "schema": {
    "type": "object",
    "properties": {
      "id": { "type": "string" }
    },
    "required": ["id"]
  }
}
```
*   **Response (201 Created):**
```json
{
  "tool_id": "uuid-5678",
  "status": "active"
}
```

---

## 3. Widget Endpoints (External / Customer-Facing)

### 3.1. Stream Chat (Server-Sent Events)
*   **Endpoint:** `POST /api/v1/chat/stream`
*   **Description:** Initiates an LLM conversation. Responds with `text/event-stream`.
*   **Request:**
```json
{
  "session_id": "uuid-abc",
  "message": "Cancel subscription for user john@example.com"
}
```
*   **Response (Streamed Events):**
    *   `event: message` | `data: {"text": "I can help with that."}`
    *   `event: hitl_required` | `data: {"tool": "delete_customer_account", "params": {"id": "john@example.com"}, "pending_action_id": "action-999"}`

### 3.2. Confirm HITL Action
*   **Endpoint:** `POST /api/v1/chat/hitl-confirm`
*   **Description:** Triggered when the user clicks the "Confirm" or "Cancel" button on the Action Required warning card in the widget.
*   **Request:**
```json
{
  "pending_action_id": "action-999",
  "decision": "approved" // or "rejected"
}
```
*   **Response (200 OK):**
```json
{
  "status": "action_resumed"
}
```
