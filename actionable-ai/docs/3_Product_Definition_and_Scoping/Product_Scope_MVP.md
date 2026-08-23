# Product Scope & Roadmap: Actionable AI (A²I) Platform

## 1. Product Vision
To provide a plug-and-play chatbot platform that dynamically builds and maintains its own knowledge base. It serves as an **Active AI Assistant** with two primary functions:
1. Answering customer queries and **executing actions** (UI navigation, data fetching, tool calling) on the company's application via an embeddable widget.
2. Assisting internal non-technical staff (sales, marketing) in understanding the product via a centralized internal dashboard.

---

## 2. Phase 1: Minimum Viable Product (MVP) - "Prove It Works Safely"
*Goal: Get a secure, working widget on a client's site answering questions and executing basic actions via manual uploads in under 2 weeks.*

### 2.1. Core System & Ingestion
- **Basic Account Management**: User registration, login, and creation of a single "Workspace".
- **Manual Knowledge Ingestion (Quick Start)**: Ability to upload text, PDF, and Markdown files to be processed by the RAG pipeline instantly, guaranteeing a Time-to-Value (TTV) under 5 minutes.

### 2.2. Chatbot Functionality & Agentic Actions
- **Embeddable Customer Widget**: A lightweight (Vanilla JS/Preact) floating widget enforcing strict **CSS Isolation** (Shadow DOM) and utilizing **DOMPurify** (XSS protection). Features Optimistic UI and **SSE Buffering** for loading states to prevent JSON jitter.
- **Agentic Tool Registration**: Developers can register client-side JS functions and backend API endpoints. All tools must be classified as Read/Write, with Write tools requiring explicit **Human-in-the-Loop (HITL) user confirmation**.
- **Secure Agent Authorization**: All tool registrations and executions strictly require a valid user context token (e.g., JWT) to authorize the action.
- **Graceful Tool Failure**: The widget handles broken JS function registrations gracefully without crashing the UI.
- **Handoff & Escalation**: Basic Email and Webhook escalation when the AI fails to answer or the user requests a human.

---

## 3. Phase 2: Version 1 (V1) - "Automation & Scale"
*Goal: Automate ingestion and protect the backend from abuse as the user base grows.*

### 3.1. Automation & CI/CD
- **Code Repository Connection**: OAuth integration with GitHub (handled asynchronously) with strict `.gitignore` checking and secret-scanning.
- **Diff-Based Syncing**: Vector DB synchronization explicitly handles code deletions to prevent stale knowledge hallucinations.

### 3.2. Cost Control & Resiliency
- **Semantic Caching & Rate Limiting**: Strict limits per IP/Workspace to prevent token exhaustion. Caching returns answers for identical queries without hitting the LLM.
- **API Exponential Backoff**: The API Request Engine handles 3rd party API failures gracefully.
- **SSRF Egress Filtering**: Backend service blocks internal IP/AWS metadata resolution for security.
- **Agent Orchestration Limits**: Max iteration caps (e.g., max 5) to prevent DoW recursive tool loops.
- **State Memory**: Robust state management (e.g., LangGraph) for multi-turn conversations.

---

## 4. Phase 3: Version 2 (V2) - "Enterprise Polish & Safety"
*Goal: Achieve SOC2 compliance and solve advanced RAG/Orchestration edge cases to close enterprise deals.*

### 4.1. Advanced Orchestration, Security & UI
- **Re-ranking Pipeline**: (e.g., Cohere ReRank) applied to the Vector DB to prevent LLM context exhaustion.
- **LLM Abstraction Layer**: (e.g., LiteLLM) to prevent vendor lock-in and allow model swapping.
- **Input Guardrails**: Active filtering system (e.g., LlamaGuard) to block malicious prompt injections.
- **PII Scrubbing Middleware**: Redacting sensitive information before storing in Query Logs for GDPR/SOC2 compliance.
- **"Show Me How" Mode**: Visual UI overlay guidance guiding users through agentic actions.

### 4.2. Helpdesk Integrations
- **Native Support APIs**: Direct ticketing integrations with platforms like Zendesk and Intercom.

---

## 5. Phase 4: Version 3 (V3) - "Global Expansion"
*Goal: Expand to international markets and support massive enterprise ecosystems.*

- **Multi-lingual Embedding Models**: For seamless cross-lingual semantic search.
- **Multi-Source Knowledge**: Integrations with Notion, Confluence, and Google Drive.
- **Proactive Chat**: Widget suggests articles/answers based on the user's current URL.
- **Multi-Step Agentic Workflows**: Chaining multiple tool calls autonomously without explicit user prompts between each step.
