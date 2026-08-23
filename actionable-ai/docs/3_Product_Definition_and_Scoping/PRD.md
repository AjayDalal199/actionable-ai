# Product Requirements Document (PRD): Actionable AI (A²I) Platform

## 1. Product Overview
A general-purpose chatbot integration platform that enables companies to easily embed an intelligent, **Agentic AI Assistant** into their applications. The chatbot leverages a Retrieval-Augmented Generation (RAG) pipeline to accurately answer user questions based on product documentation and automated codebase analysis. Furthermore, it supports **Client-Side and Server-Side Tool Calling**, allowing the AI to execute frontend functions, invoke backend client APIs directly, and perform tasks on behalf of the user.

## 2. Target Audience
- **Developers / Technical Teams**: To integrate the chatbot, connect code repositories, and manage technical documentation.
- **Product Managers / Technical Writers**: To review, edit, and manage the auto-generated and manually uploaded product documentation.
- **Sales & Marketing / Non-Technical Staff**: To use the internal chatbot for answering product-related questions and learning about new features.
- **End Users (Customers)**: The people interacting with the integrated chatbot on the client's application.

## 3. Core Features

### 3.1. Knowledge Ingestion & Management
- **Manual Document Upload [MVP]**: Users can provide existing product information, FAQs, and documentation.
- **Code Repository Integration [V1]**: Users can securely connect their code repositories (e.g., GitHub, GitLab).
- **Automated Feature Discovery [V1]**: The system scans the connected codebase to automatically generate *Technical Documentation*. For *Customer-Facing Documentation*, it relies on analyzing Pull Request descriptions, Jira tickets, and uploaded PDFs.
- **Continuous Integration (Auto-Documentation) [V1]**: Whenever a user pushes updates to specified branches (e.g., `develop`, `master`), the system automatically triggers the feature discovery pipeline asynchronously.
- **Manual Pipeline Trigger [V1]**: The feature discovery and documentation generation pipeline can also be triggered manually.
- **Multi-Source Knowledge [V3]**: Notion, Confluence, Google Drive syncs.

### 3.2. Documentation Types
The system maintains distinct types of documentation to serve different contexts:
- **Technical Documentation [V1]**: Detailed system architecture, API references, and code-level explanations derived from the codebase.
- **Customer-Facing Documentation [MVP]**: User-friendly guides and knowledge base articles used by the chatbot to answer end-user queries safely and effectively.

### 3.3. RAG Pipeline, Agentic Action & Chatbot
- **Customer Chatbot (External & Agentic) [MVP]**: A chatbot widget that answers queries and supports **Agentic Tool Execution**. Tools must be classified as "Read-Only" or "Write" (requiring HITL confirmation).
- **Human Handoff & Escalation [MVP]**: Email/Webhook fallback mechanism. Native integrations (Zendesk/Intercom) are deferred to **[V2]**.
- **Internal Chatbot [MVP]**: A chatbot available within our platform's dashboard.
- **Proactive Chat [V3]**: Widget suggests answers based on URL.
- **"Show Me How" Mode [V2]**: Visual UI overlay guidance for agentic actions.
- **Multi-Step Agentic Workflows [V3]**: Chaining tool calls autonomously.

### 3.4. Integration Support
- **Integration Guides [MVP]**: Step-by-step instructions.
- **Backend API Integration (Server-to-Server) [MVP]**: Support for registering backend API endpoints securely.

### 3.5. User, Access, & Agent Security (RBAC)
- **Secure Agent Authorization [MVP]**: The widget requires a signed JWT to ensure authorized actions.
- **Input Guardrails [V2]**: Active filtering (e.g., LlamaGuard) to block prompt injection.
- **Role-Based Access Control [MVP]**: Managers/Admins, Editors, Viewers.

### 3.6. Cost Control & Compliance
- **LLM Rate Limiting & Caching [V1]**: Strict limits per IP/Workspace and Semantic Caching.
- **Data Privacy & PII Scrubbing [V2]**: Middleware to scrub PII for GDPR/SOC2.

## 4. User Flows
1. **Onboarding**: A company manager creates an account, uploads initial docs, and connects their code repository.
2. **Knowledge Generation**: The system scans the codebase, performs feature discovery, and generates the initial technical and customer documentation.
3. **Review & Edit**: Team members with edit permissions review the generated docs, make necessary adjustments, and approve them.
4. **Integration & Tool Registration**: Developers follow the generated steps to add the floating widget to their application. They also register their frontend JavaScript functions and backend API endpoints with the platform so the AI Assistant can perform actions.
5. **Continuous Update**: Developers push new code to the `master` branch. The system detects the change, runs the feature discovery pipeline, updates the docs, and ensures the chatbot is answering questions based on the latest features.
6. **Escalation & Support**: When an end-user asks a question outside the Assistant's knowledge base, the system triggers a handoff, collecting the user's email and forwarding the chat history to the company's human support team.

## 5. Technical Requirements (High-Level)
- **Vector Database [MVP/V1]**: Storing document embeddings (MVP). Paired with **Re-ranking Pipeline [V2]** (e.g., Cohere) and **Context Sanitization [V1]**. Multi-lingual embeddings deferred to **[V3]**.
- **LLM Integration [MVP]**: Core LLM usage (MVP). **Input Token Truncation [MVP]** to prevent crashes. **LLM Abstraction Layer [V2]** (e.g., LiteLLM).
- **Webhook Integration [V1]**: For GitHub/GitLab webhooks.
- **Tool Schema Validation & Error Handling [MVP]**: Graceful error handling on the frontend.
- **API Request Engine & State Management [MVP/V1]**: Server API calls (MVP). **Strict Egress Filtering (SSRF protection) [V1]**. **Agent Orchestration Limits (DoW protection) [V1]**. **State Memory (LangGraph) [V1]**.
- **Frontend Widget [MVP]**: Lightweight (Vanilla JS/Preact), CSS Isolation (Shadow DOM), DOMPurify (XSS), SSE Buffering, Optimistic UI.
