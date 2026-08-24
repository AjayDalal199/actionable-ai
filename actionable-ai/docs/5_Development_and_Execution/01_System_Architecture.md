# 01 System Architecture

## Document Metadata

- **Status:** Approved (high-level product architecture)
- **Scope:** Forward-Looking (Supports MVP & V1)
- **Last Updated:** 2026-08-25

**Code layout:** Frontend is **Option A** — [05 Frontend Architecture](./05_Frontend_Architecture.md). Backend is **Option B** (modular monolith) — [06 Backend Architecture](./06_Backend_Architecture.md).

The diagram below is the *product* split (dashboard, widget, APIs, Postgres, Redis). The backend in this repo is **one FastAPI app**. MVP/V1 stays a modular monolith (doc 06). Do not split into microservices unless we change that decision.

---

## 1. High-Level Architecture Overview

The Actionable AI (A²I) platform utilizes a modern, decoupled microservices architecture. The system is split into three core layers: The Presentation Layer (Landing Page, Widget, Dashboard), the Orchestration API Layer (FastAPI Backend), and the Persistence Layer (PostgreSQL/pgvector).

```mermaid
graph TD
    subgraph Presentation Layer
        F[Unified Frontend (React/Vite)]
        W[Embeddable Widget (Web Component)]
    end

    subgraph API Layer (FastAPI)
        C[Chat Orchestrator]
        K[Knowledge API]
        T[Tool Registry API]
    end

    subgraph Data & AI Persistence
        LLM[LLM Gateway / LangGraph]
        PG[(PostgreSQL + pgvector)]
        R[(Redis - Pub/Sub for SSE)]
    end

    W -->|Streaming SSE + HITL Actions| C
    F -->|Upload Docs| K
    F -->|Register JSON Schemas| T

    C --> LLM
    K --> LLM
    T --> PG

    LLM <--> PG
    C -.->|Async Messaging| R
```

## 2. Component Stack

### 2.1. Presentation Layer (Frontend)

- **Unified Frontend (React/Vite):** A single application using Tanstack Router. The public landing page is served at the root (`/`), acting as the marketing site. The authenticated B2B Dashboard is served at `/dashboard`, used by administrators to upload documents and register API tools. Built with React 18, Vite, Tailwind CSS, and Shadcn UI.
- **Embeddable Widget:** Built as a Vanilla JavaScript Web Component using the Shadow DOM. This strictly isolates the widget's CSS, ensuring it never leaks into or inherits from the host customer's website styling.

### 2.2. API Layer (Backend)

- **Framework:** FastAPI (Python 3.11+). Chosen for its high performance, native async support, and automatic OpenAPI schema generation.
- **Orchestration:** LangGraph. Used to orchestrate complex LLM agent workflows, specifically pausing state for Human-in-the-Loop (HITL) approvals.
- **Communication:** Server-Sent Events (SSE) for streaming LLM responses to the widget.

### 2.3. Persistence Layer (Database)

- **Primary Database:** PostgreSQL 16.
- **Vector Engine:** pgvector extension for storing and querying document embeddings (RAG).
- **ORM:** SQLModel (by Tiangolo). Provides seamless integration between FastAPI validation and SQLAlchemy database models.
- **Cache / Messaging:** Redis. Used for rate limiting and managing Pub/Sub events when an agent is awaiting human approval.

## 3. Core Workflows

### 3.1. RAG Ingestion Pipeline

1. Dashboard uploads a PDF/Markdown file.
2. FastAPI chunks the document and sends chunks to the Embedding Model.
3. FastAPI stores the text chunk and its vector representation in the `DocumentChunk` table via pgvector.

### 3.2. Agent Tool Execution & HITL

1. User asks the widget to perform an action (e.g., "Delete Project X").
2. LLM determines it needs to call the `delete_project` tool.
3. LangGraph pauses execution because the tool is flagged as `requires_hitl: True`.
4. FastAPI sends an "Action Required" card via SSE to the widget.
5. User clicks "Confirm". Widget sends a POST request back to FastAPI.
6. LangGraph resumes state, executes the API call, and streams the final success message to the user.
