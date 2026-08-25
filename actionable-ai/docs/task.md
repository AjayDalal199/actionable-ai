# Actionable AI (A²I) — MVP Task List

**Product:** Actionable AI (A²I) Platform  
**Phase:** MVP — “Prove it works safely”  
**Goal:** A developer can sign up, upload docs, register a tool, paste one script tag, and have a live in-product agent that answers from their knowledge *and* executes actions with Human-in-the-Loop (HITL) on writes. Time-to-value under 5 minutes.

**Legend:** `[x]` done · `[/]` in progress · `[ ]` not started

**Architecture (locked 2026-08-25):** Frontend [Option A](./5_Development_and_Execution/05_Frontend_Architecture.md) — keep `frontend/` as-is; widget later in `packages/widget`. Backend [Option B](./5_Development_and_Execution/06_Backend_Architecture.md) — modular monolith (`app/models/` package, `app/services/`, thin routes). One task at a time.

---

## Next up (do this only)

**Task:** Phase 1.3 dashboard shell. Do not start Knowledge APIs yet.

- `[ ]` Sidebar: Dashboard (Quick Start), Knowledge, Tools, Chat (internal), Settings — drop Items from nav
- `[ ]` Empty-state home: “Name your workspace → upload a doc → ask a question” (create-workspace CTA if they have none)

**Done when:** Logged-in product nav matches the real app, not the template Items dashboard.

**After that (not now):** Phase 1.2 invite/RBAC APIs, or Phase 2 data plane — follow the path-to-MVP order (RBAC remaining, then data plane).

---

## What MVP must prove

A beta client can put a working widget on a staging site that:

1. Answers questions from **manually uploaded** PDFs and Markdown (RAG).
2. Executes **registered tools** (client JS functions and server APIs).
3. **Never** runs a write/destructive action until the end-user confirms it in the widget, in plain language.
4. Authorizes actions with a **signed end-user JWT** from the host app.
5. Escalates to a human via **email or webhook** when it cannot help.

If those five are true, we have an MVP. Everything else is V1+.

---

## Explicitly out of scope for MVP

Do not start these until MVP ships. They are documented so they do not leak into this list.

| Deferred | When | Why it is not MVP |
| --- | --- | --- |
| GitHub / GitLab OAuth, webhooks, auto-doc from PRs | V1 | Manual upload is the 5-minute path |
| `GithubRepository` sync workers, diff-based reindex | V1 | Schema only in MVP |
| Semantic caching, LLM abstraction (LiteLLM) | V1 / V2 | Cost control beyond a basic cap |
| Re-ranking (Cohere), LlamaGuard, PII scrubbing | V2 | Quality / compliance polish |
| Zendesk / Intercom native tickets | V2 | Email + generic webhook is enough |
| “Show me how” overlays, proactive chat, multi-step autonomous workflows | V2 / V3 | Extra agent UX |
| Notion / Confluence / Drive, multi-lingual embeddings | V3 | Extra ingestion |
| Pricing page, blog, changelog, SSO | later | Not required to prove the agent |

---

## Current state (as of 2026-08-25)

We are still on the Full Stack FastAPI template plus a public marketing site. Auth works. Architecture is decided. The product domain (workspaces, knowledge, tools, chat, widget) is not built.

**Already in place**

- `[x]` FastAPI backend in `./backend` (users, login, JWT, password recovery)
- `[x]` React / Vite dashboard in `./frontend` (TanStack Router, shadcn/ui, Tailwind)
- `[x]` PostgreSQL + SQLModel + Alembic (no pgvector yet)
- `[x]` Public landing page at `/` (ember brand, HITL artifact, logged-in redirect to `/dashboard`)
- `[x]` `/signup`, `/login`, `/recover-password`, `/terms`, `/privacy`
- `[x]` Wordmark **Actionable AI** in chrome
- `[x]` Superuser admin (template user CRUD — not workspace RBAC)
- `[x]` Frontend architecture Option A (dashboard stays; widget = `packages/widget` later)
- `[x]` Backend architecture Option B (modular monolith; `app/models/` package in place)

**Still template leftovers (must be replaced, not shipped as product)**

- `[ ]` Remove demo **Items** CRUD from dashboard and API (or hide it) once Knowledge / Tools exist
- `[ ]` Replace template dashboard home with the Quick Start / sandbox flow
- `[ ]` Hide Items from the sidebar when the dashboard shell is updated (Phase 1.3) — do not delete the API in the models-package slice

---

## Path to MVP

Work in this order. Later phases depend on earlier ones. Dashboard UI can trail its matching API by a sprint, but do not start the widget until chat streaming exists.

```text
1. Workspace + RBAC
        ↓
2. Data plane (pgvector, Redis, core tables)
        ↓
3. Knowledge ingestion  ──┐
        ↓                 │
4. Tool registry          ├── 5. Chat orchestrator (RAG + tools + HITL + SSE)
        ↓                 │
6. Embeddable widget  ←───┘
        ↓
7. Dashboard product (upload UI, tools UI, sandbox, snippet, internal chat)
        ↓
8. Handoff + launch safety + QA
        ↓
     MVP ship
```

---

## Phase 1 — Multi-tenant foundation (Workspace + RBAC)

**Why first:** Every later table is scoped by `workspace_id`. Chat, uploads, and tools are unsafe without tenant isolation.

**Layout (Option B):** `app/models/` for tables, `app/services/` for business rules, thin `app/api/routes/`. Do not add Workspace to the old single `models.py` file.

**Done when:** A new user can sign up without a workspace (join via invite later), or create one and become its Admin, and cannot see another workspace’s data.

### 1.0 Models package

Mechanical split. No schema change.

- `[x]` Create `app/models/` package (`user.py`, `item.py`, `auth.py`, `base.py`)
- `[x]` Keep `from app.models import …` working via `__init__.py` re-exports
- `[x]` Alembic still uses `from app.models import SQLModel`
- `[x]` No schema change, no Alembic revision; pytest 60 passed

### 1.1 Workspace model and APIs

Do these **after** 1.0, one checkbox group per reviewable slice.

- `[x]` Add `app/models/workspace.py` — `Workspace` (`id`, `name`, `created_at`) only; no User FK yet
- `[x]` Alembic migration creating the `workspace` table (still no user columns)
- `[x]` Add `workspace_id` + `role` on `User`; Alembic migration; signup/service comes next
- `[x]` `CurrentWorkspace` dependency (from session user, not a client-supplied id)
- `[x]` `app/services/` — signup does **not** auto-create a workspace (join-via-invite later). Optional `workspace_name` on signup, or `POST /workspaces/`, creates one and attaches the user as **Admin**
- `[x]` `GET /api/v1/workspaces/me` — current workspace for the session
- `[x]` `PATCH /api/v1/workspaces/me` — rename (Admin only)
- `[ ]` All product queries filter by `workspace_id` from `CurrentWorkspace` (never trust a client-supplied workspace id without membership check)

### 1.2 Users inside a workspace (RBAC)

MVP roles (from PRD): **Admin**, **Editor**, **Viewer**.

| Role | Can do |
| --- | --- |
| Admin | Billing-level: invite, change roles, workspace settings, all Editor powers |
| Editor | Upload/delete docs, register/edit tools, use internal chat, copy widget snippet |
| Viewer | Read docs/tools, use internal chat, cannot mutate config |

- `[x]` Add `workspace_id` + `role` on `User` (or a `WorkspaceMembership` table if we want multi-workspace later; **MVP = one workspace per user**)
- `[ ]` Replace template `is_superuser`-only gates for product routes with role checks
- `[ ]` Keep platform `is_superuser` for *our* ops admin only (not client Admin)
- `[ ]` Invite flow (MVP-simple): Admin adds a user by email + role; invited user sets password via existing email recovery/invite mail
- `[ ]` List workspace members; Admin can change role or deactivate
- `[ ]` Tests: cross-tenant isolation (user A cannot read user B’s documents/tools/chat)

### 1.3 Dashboard shell for a real product

- `[ ]` Sidebar: Dashboard (Quick Start), Knowledge, Tools, Chat (internal), Settings — drop Items from nav
- `[ ]` Empty-state home: “Name your workspace → upload a doc → ask a question”

---

## Phase 2 — Data plane for RAG and HITL

**Why now:** Ingestion and the agent both need vectors and a place to pause HITL state.

**Done when:** Postgres has pgvector, Redis is in Compose, and the schema in `02_Database_Schema.md` exists (including forward-looking `GithubRepository` with **no** sync logic).

### 2.1 PostgreSQL + pgvector

- `[ ]` Enable `pgvector` on the app database (image/extension in Docker; local + deploy docs)
- `[ ]` Confirm vector dimension (OpenAI `text-embedding-3-small` = 1536 unless we choose otherwise) and document it in config
- `[ ]` Add `Document` (`workspace_id`, `title`, `type` pdf/markdown/text, `status` processing/active/failed, `original_filename`, `error_message`, `created_at`)
- `[ ]` Add `DocumentChunk` (`document_id`, `content`, `embedding` vector, `chunk_index`, optional `metadata` JSONB)
- `[ ]` IVFFlat or HNSW index on `embedding` (start with a simple index; tune later)
- `[ ]` Add `ToolRegistry` (`workspace_id`, `name` unique per workspace, `kind` http/js, `http_method`, `url`, `schema` JSONB, `requires_hitl`, `description`, `is_active`)
- `[ ]` Add `GithubRepository` **table only** (`workspace_id`, `url`, `target_branch`, `last_sync`) — no OAuth, no workers
- `[ ]` Alembic migrations + model tests

### 2.2 Redis

- `[ ]` Add Redis service to `compose.yml` / deploy compose
- `[ ]` App settings: `REDIS_URL`
- `[ ]` Use Redis for: HITL pending-action state, SSE/pubsub if needed, and a **basic** rate-limit counter (Phase 8)
- `[ ]` Health check includes Redis

### 2.3 Object / file storage for uploads

- `[ ]` Decide store: local volume for MVP Docker, S3-compatible later — document the choice
- `[ ]` Persist original file bytes keyed by `document_id` (needed to re-process on failure)
- `[ ]` Max size **10MB** to match the Knowledge UI spec (API contract said 50MB — **implement 10MB** and update the API contract)

---

## Phase 3 — Knowledge ingestion (RAG write path)

**Why now:** TTV is “upload → ask.” Nothing else matters until a file becomes searchable chunks.

**Done when:** Editor uploads a PDF or `.md`, status goes Processing → Active (or Failed), and chunks are queryable with cosine similarity.

### 3.1 Embedding + chunking pipeline

- `[ ]` Config: `OPENAI_API_KEY`, embedding model, chat model
- `[ ]` Extract text: Markdown as-is; PDF via a maintained extractor (fail the document if extract is empty)
- `[ ]` Chunk with overlap (document chosen sizes, e.g. ~500–800 tokens, overlap ~10–20%)
- `[ ]` Embed chunks; store in `DocumentChunk`
- `[ ]` Run ingestion **asynchronously** (background task / worker) so the upload API returns immediately with `status: processing`
- `[ ]` Idempotent re-process: replacing a document deletes old chunks then re-embeds
- `[ ]` Duplicate filenames: auto-append timestamp (UI spec decision)
- `[ ]` Input token / file safety: skip empty files; cap pages/chars so one upload cannot melt the worker

### 3.2 Knowledge APIs (dashboard)

Align with `03_MVP_API_Contracts.md`, plus list/status that the UI needs.

- `[ ]` `POST /api/v1/knowledge/upload` — multipart, workspace from auth, returns `{ document_id, status: "processing" }`
- `[ ]` `GET /api/v1/knowledge/documents` — list for the table (name, date, status)
- `[ ]` `GET /api/v1/knowledge/documents/{id}` — detail + error message if failed
- `[ ]` `DELETE /api/v1/knowledge/documents/{id}` — delete file + chunks
- `[ ]` AuthZ: Editor+ to mutate; Viewer can list
- `[ ]` Reject non-pdf / non-md / non-txt; reject > 10MB
- `[ ]` Tests: upload happy path, isolation, invalid type, failed parse sets `failed`

### 3.3 Knowledge Base UI (dashboard)

Spec: `docs/4_Design_and_Prototyping/MVP/Dashboard/01_Quick_Start_and_Ingestion.md`

- `[ ]` Route `/dashboard/knowledge`
- `[ ]` Table: file name, date, status badges (Active / Processing / Failed)
- `[ ]` Empty state + CTA “Upload Data”
- `[ ]` Side panel: drag-and-drop, click to browse, determinate progress
- `[ ]` Client-side type/size validation; toast on network interrupt
- `[ ]` Multi-file upload in one drop
- `[ ]` Poll (or lightweight SSE) so status flips without refresh
- `[ ]` Failed row: tooltip with `error_message`
- `[ ]` Keyboard + `sr-only` status text (spec §11)

---

## Phase 4 — Tool registry (give the agent hands)

**Why now:** The orchestrator must load a typed tool list per workspace. HITL flags live on the tool, not in the prompt.

**Done when:** An Editor can register an HTTPS (or localhost) endpoint with a JSON schema; POST/PUT/DELETE lock HITL on; the tool is available in sandbox chat.

### 4.1 Tool APIs

- `[ ]` `POST /api/v1/tools/register` — body per API contract; force `requires_hitl=true` for POST/PUT/DELETE even if client sends false
- `[ ]` `GET /api/v1/tools` — list
- `[ ]` `GET /api/v1/tools/{id}`
- `[ ]` `PATCH /api/v1/tools/{id}` — edit schema/url/description
- `[ ]` `DELETE /api/v1/tools/{id}` (or deactivate)
- `[ ]` Validate: `name` snake_case `^[a-z0-9_]+$`; unique per workspace (409)
- `[ ]` Validate JSON Schema is an object with `type` / `properties`
- `[ ]` Tool kinds for MVP:
  - **HTTP:** method + URL + schema (server-side execution via our API Request Engine)
  - **JS:** name + schema only (execution happens in the host page; we emit a tool-call event to the widget)
- `[ ]` Tests: HITL hard-lock, 409 duplicate, Viewer cannot register

### 4.2 API Request Engine (server-side tools)

MVP needs real HTTP calls. Full SSRF hardening is V1; **do the minimum now** so we do not fetch metadata IPs.

- `[ ]` HTTP client with timeouts
- `[ ]` Block obvious SSRF: localhost, link-local, private RFC1918, AWS/GCP metadata hosts (expand in V1)
- `[ ]` HTTPS required except `localhost` for integrator testing
- `[ ]` Pass through the **end-user JWT** (Phase 6) as `Authorization: Bearer` (or a documented header) to the client API — we do not invent permissions
- `[ ]` Map non-2xx to a structured error the LLM can explain (no fake success)
- `[ ]` Simple retry: once on 502/503; no infinite loops

### 4.3 Tools & Actions UI (dashboard)

Spec: `docs/4_Design_and_Prototyping/MVP/Dashboard/02_Tool_Registration_Flow.md`

- `[ ]` Route `/dashboard/tools`
- `[ ]` Table: name, type (GET / JS / …), safety (Read only vs HITL)
- `[ ]` Side panel: name, URL (HTTP), method, description, Monaco JSON schema editor
- `[ ]` Changing method to POST/PUT/DELETE: HITL toggle ON and **disabled**
- `[ ]` Save disabled on invalid JSON or invalid name
- `[ ]` Unsaved-changes confirm when closing the panel
- `[ ]` Duplicate-name inline error from 409

---

## Phase 5 — Chat orchestrator (the product brain)

**Why now:** Sandbox, internal chat, and the widget all share one streaming API.

**Done when:** A message streams tokens; questions hit RAG; write tools pause for HITL; confirm resumes and completes; reject aborts.

Specs: architecture §3.2, `03_MVP_API_Contracts.md`, `04_MVP_LLM_Prompts.md`.

### 5.1 Session and streaming API

- `[ ]` `ChatSession` (or Redis-backed session) keyed by `session_id` + `workspace_id`
- `[ ]` Persist messages enough to resume HITL and to attach a transcript on escalation
- `[ ]` `POST /api/v1/chat/stream` — `text/event-stream`
  - Request: `{ session_id, message, channel?: "widget" | "internal" }`
  - Events: `message` (token/text), `hitl_required`, `tool_js` (client-side function), `error`, `done`
- `[ ]` `POST /api/v1/chat/hitl-confirm` — `{ pending_action_id, decision: "approved" | "rejected" }` → resume or abort
- `[ ]` Widget channel: require **host end-user JWT** (Phase 6), not only the integrator’s dashboard JWT
- `[ ]` Internal/sandbox channel: require logged-in workspace member
- `[ ]` Truncate user text (UI ~2000 chars; backend hard cap ~2000 tokens) **before** embed/LLM
- `[ ]` Max tool iterations per turn (e.g. 5) so the graph cannot loop

### 5.2 RAG retrieval (read path)

- `[ ]` Embed the query with the same model as ingestion
- `[ ]` Top-k similarity search **scoped to workspace_id** (join through Document)
- `[ ]` Only `status=active` documents
- `[ ]` Wrap retrieved text in delimiters; system prompt: retrieved text is data, never instructions (cheap anti-injection for MVP)
- `[ ]` If similarity is below a threshold, prefer “I don’t know” / handoff rather than guessing
- `[ ]` Input token truncation of the *context pack* so the prompt cannot blow the model window

### 5.3 LangGraph agent

- `[ ]` Graph nodes: retrieve → reason → tool or answer → (HITL interrupt) → execute → answer
- `[ ]` Load workspace tools as LLM functions from `ToolRegistry`
- `[ ]` Inject `request_hitl_approval` schema from `04_MVP_LLM_Prompts.md`
- `[ ]` **Code-enforced** HITL: if tool `requires_hitl` and the model tries to call it directly, intercept and convert to HITL (do not trust the model)
- `[ ]` On HITL: pause graph, store state in Redis under `pending_action_id`, emit `hitl_required` with **plain-language** title/summary only (no HTTP method, path, tool id, or “API”)
- `[ ]` On approve: execute HTTP tool or emit JS tool event; stream success/failure
- `[ ]` On reject: stream “No problem, I won’t do that.”; do not retry the same write quietly
- `[ ]` System prompt from `04_MVP_LLM_Prompts.md` (tune voice: customer widget vs internal dashboard)
- `[ ]` Graceful LLM/provider errors → stable `error` SSE event

### 5.4 Client-side (JS) tools

- `[ ]` Registry entry has no URL; widget is told `{ name, arguments }`
- `[ ]` Widget looks up `window`/`registerTool` map; on missing/throw, show fallback text (do not crash)
- `[ ]` Writes still go through HITL **before** the widget invokes the JS function

---

## Phase 6 — Embeddable customer widget

**Why now:** This is the surface beta clients actually ship. It consumes Phase 5.

**Done when:** A host page loads one script, opens a Shadow DOM chat, streams answers, shows HITL in plain language, and confirms/rejects safely.

Spec: `docs/4_Design_and_Prototyping/MVP/Widget/01_Core_Chat_and_HITL_Flow.md`

### 6.1 Package and isolation

- `[ ]` New package **`packages/widget`** (Option A) — Vanilla JS or Preact, **not** the full dashboard React app; no import from `frontend/src` or `@/shared/ui`
- `[ ]` Web Component + **Shadow DOM** (host `button { }` must not restyle us)
- `[ ]` Sanitize rendered Markdown (`marked` + **DOMPurify**)
- `[ ]` Async loader / small bundle; document a target size and fail CI if we explode it
- `[ ]` Public script URL (CDN or `/widget.js` from our origin) + snippet with `data-workspace` / public key

### 6.2 Secure agent authorization

- `[ ]` Integrator initializes with a **signed JWT from their backend** representing the *end-user*
- `[ ]` Document the claims we require (sub, expiry, optional email); we verify signature with the workspace’s configured secret/JWKS
- `[ ]` No JWT → chat may answer RAG **read-only** or show “sign in” — **no write tools**
- `[ ]` Expired/invalid JWT → refuse tools; explain in the widget
- `[ ]` Never accept the integrator dashboard token as end-user identity

### 6.3 Chat UX

- `[ ]` FAB bottom-right; modal open/close; session history kept in memory while the tab lives
- `[ ]` Composer: Enter send, Shift+Enter newline, 2000-char truncate
- `[ ]` Optimistic 3-dot loader the moment Send is pressed; drop it on first SSE chunk
- `[ ]` SSE buffering so partial JSON does not flicker
- `[ ]` HITL card: action title, consequence, optional “Cannot be undone”, **Go back** / **Confirm** — never endpoints
- `[ ]` Confirm/Go back disable that card permanently
- `[ ]` Desktop ~380×700; mobile full viewport
- `[ ]` `role="log"` / `aria-live` for messages; HITL `assertive`
- `[ ]` Connection loss copy from spec; timeouts do not freeze the composer forever

### 6.4 JS tool bridge + failure

- `[ ]` `A2I.registerTool(name, fn)` (or equivalent) on the host
- `[ ]` Catch throws / missing fn → user-visible fallback, widget stays up

### 6.5 Dashboard: snippet export

- `[ ]` Settings or Quick Start: copy `<script src="…">` + init example
- `[ ]` Show workspace public id and how to mint the end-user JWT (short integration guide)

---

## Phase 7 — Dashboard product complete (Quick Start loop)

**Why now:** TTV is measured here: signup → upload → sandbox question → copy snippet.

**Done when:** A new Admin can finish that loop without leaving the app or reading a separate PDF.

### 7.1 Quick Start + sandbox

Journey 1 in `User_Journeys.md`.

- `[ ]` After first workspace: guided steps (upload → ask → copy snippet)
- `[ ]` **Sandbox chat** on dashboard using the same orchestrator as the widget (`channel: internal` or `sandbox`)
- `[ ]` Redirect/focus sandbox when the first document becomes Active (target: usable within ~60s of upload)
- `[ ]` Sandbox may use the dashboard user as identity; label it clearly as a test surface

### 7.2 Internal chatbot

PRD: internal chatbot is MVP (Marcus / sales-support).

- `[ ]` Route `/dashboard/chat` — full-page chat, same APIs, workspace RAG + tools
- `[ ]` Default to read-heavy behavior; still HITL if someone tests a write tool
- `[ ]` Empty state if no documents: point to Knowledge upload

### 7.3 Widget preview (optional but useful)

- `[ ]` Dashboard page that mounts the real widget against the current workspace (staging key) so David does not need a second app on day one

---

## Phase 8 — Handoff, launch safety, and compliance-minimum

**Why now:** A widget that silently fails or burns tokens is not shippable.

**Done when:** Low-confidence / “talk to a human” collects email, sends transcript, and the service cannot be trivially bankrupted or SSRF’d.

### 8.1 Human handoff (email + webhook)

Journey 4. Native Zendesk is V2.

- `[ ]` Workspace settings: support email, optional webhook URL, enable/disable
- `[ ]` Trigger: user asks for a human, or retrieval confidence too low, or agent admits it does not know
- `[ ]` Widget: ask for best email; do not block forever if they refuse — still offer retry
- `[ ]` Bundle: transcript, workspace id, session id, user email, timestamp
- `[ ]` Send email to the workspace support address
- `[ ]` POST JSON to the webhook (timeout, sign with a shared secret header)
- `[ ]` Log handoff events for us (no PII scrubbing until V2 — minimize what we store; do not log passwords if we can detect them naively)

### 8.2 Launch safety (subset of P0/P1 — not the full V1 platform)

Product Scope puts full rate limits / semantic cache / SSRF / DoW in V1. MVP still needs a floor:

- `[ ]` Per-IP and per-workspace **request caps** on `/chat/stream` (Redis). Fail closed with a clear error
- `[ ]` Daily or monthly **soft LLM budget** per workspace (env-configured) so a viral page cannot create a surprise five-figure bill
- `[ ]` HITL hard-lock tested as a security test, not only a UX test
- `[ ]` Tenant isolation tests on chat, knowledge, tools
- `[ ]` Minimum SSRF denylist on the API Request Engine (Phase 4.2)
- `[ ]` Max graph iterations (Phase 5.1)
- `[ ]` Do **not** claim SOC2/GDPR/LlamaGuard on the marketing site (already specified)

### 8.3 Observability (enough to debug beta)

- `[ ]` Structured logs: workspace_id, session_id, document_id, tool_name (not raw user PII in log aggregators if avoidable)
- `[ ]` Sentry already in template — tag new routes
- `[ ]` Metrics: chat requests, HITL shown/confirmed/rejected, handoffs, ingestion failures (even if only logs + a simple admin query)

---

## Phase 9 — Integration experience and public docs

**Done when:** An integrator can implement the widget from in-app copy + a short public doc, without a sales call.

- `[ ]` In-app **Integration** panel: script tag, JWT minting example (one language, e.g. Node or Python), `registerTool` example, CORS notes
- `[ ]` Public `/docs` **only if** it is real; otherwise omit nav links (landing spec)
- `[ ]` CORS: allow customer origins or documented `*` for widget API with JWT
- `[ ]` Example host page in-repo (`examples/host-app`) used in QA

---

## Phase 10 — Quality, polish, ship

**Done when:** The checklist below is true and we can onboard a beta client on staging.

### 10.1 Tests

- `[ ]` Backend: authz matrix, upload pipeline, tool HITL lock, chat stream (mocked LLM), hitl-confirm, handoff
- `[ ]` Widget: open/close, loader, HITL disable-after-click, Shadow DOM smoke (Playwright against example host)
- `[ ]` Dashboard: upload validation, tool form lock, sandbox send
- `[ ]` Load-ish: one scripted flood against rate limit to prove it trips

### 10.2 Product cleanup

- `[ ]` Remove or fully hide template Items feature
- `[ ]` Dashboard home is Quick Start, not empty template cards
- `[ ]` Env sample: OpenAI, Redis, widget JWT secret, file storage
- `[ ]` Deploy: Redis + pgvector on compose/cloud; document operator steps
- `[ ]` Brand: Actionable AI everywhere (emails, titles, `PROJECT_NAME`)

### 10.3 MVP acceptance (end-to-end)

A stranger (or us pretending to be David) can:

- `[ ]` Sign up, name workspace
- `[ ]` Upload `faq.md` + a PDF; both become Active
- `[ ]` Ask sandbox a question only answered in the PDF — get a grounded answer
- `[ ]` Register `cancel_subscription` DELETE with HITL locked
- `[ ]` Ask to cancel → HITL card in **plain language** → Confirm → mock API receives JWT and returns success
- `[ ]` Go back on HITL → no API call
- `[ ]` Paste snippet into `examples/host-app`, open widget, same flows
- `[ ]` Ask something unknowable → email/webhook handoff with transcript
- `[ ]` Second account cannot see the first workspace’s docs or tools
- `[ ]` Broken JS tool does not white-screen the host page

---

## Suggested build order (sprints)

Use this if you want a calendar-shaped path. Durations assume a small team; adjust, do not skip dependencies.

| Sprint | Focus | Exit |
| --- | --- | --- |
| **A0** | Phase 1.0: `app/models/` package split | **Done** — imports and tests green; DB schema unchanged |
| **A** | Phase 1–2: workspace, RBAC, pgvector, Redis, schema | Isolated tenants, empty product tables |
| **B** | Phase 3: ingestion API + Knowledge UI | Upload → Active chunks |
| **C** | Phase 4 + 5 without widget: tools API/UI + orchestrator + sandbox | Sandbox Q&A + HITL against a mock HTTP tool |
| **D** | Phase 6–7: `packages/widget`, JWT, snippet, internal chat | Script tag on example host |
| **E** | Phase 8–10: handoff, caps, tests, remove Items, beta dry-run | MVP acceptance checklist all green |

---

## Definition of done — MVP

The MVP is done when **Phase 10.3** passes on a shared staging environment, not when individual tickets are closed. Marketing already says “live in minutes”; the implementation must match that sentence.
