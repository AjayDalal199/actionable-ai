# Actionable AI (A²I) — MVP Task List

**Product:** Actionable AI (A²I) Platform
**Phase:** MVP — “Prove it works safely”
**Goal:** A developer can sign up, upload docs, register a tool, paste one script tag, and have a live in-product agent that answers from their knowledge *and* executes actions with Human-in-the-Loop (HITL) on writes. Time-to-value under 5 minutes.

**Legend:** `[x]` done · `[/]` in progress · `[ ]` not started

**Architecture (locked 2026-08-25):** Frontend [Option A](./5_Development_and_Execution/05_Frontend_Architecture.md) — keep `frontend/` as-is; widget later in `packages/widget`. Backend [Option B](./5_Development_and_Execution/06_Backend_Architecture.md) — modular monolith (`app/models/` package, `app/services/`, thin routes). One task at a time.

---


## Next up (do this only)

**Task:** Embeddable customer widget (Phase 6). Include the widget channel, JS tool execution (Phase 5.4), the snippet (6.5), and the widget preview (7.3). Do not run JS tools from the internal sandbox.

- `[ ]` Package `packages/widget`: Shadow DOM chat, end-user JWT, and the JS tool bridge
- `[ ]` Dashboard snippet export (6.5) and the widget preview (7.3)
- `[ ]` Leave `tool_js` execution out of `/dashboard/chat`

**Done when:** A host page loads one script, opens a Shadow DOM chat, streams answers, and confirms or rejects a write in plain language.

**After that (not now):** handoff and launch safety (Phase 8). See [Path to MVP](#path-to-mvp).

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


| Deferred                                                                | When    | Why it is not MVP                  |
| ----------------------------------------------------------------------- | ------- | ---------------------------------- |
| GitHub / GitLab OAuth, webhooks, auto-doc from PRs                      | V1      | Manual upload is the 5-minute path |
| `GithubRepository` sync workers, diff-based reindex                     | V1      | Schema only in MVP                 |
| Semantic caching, LLM abstraction (LiteLLM)                             | V1 / V2 | Cost control beyond a basic cap    |
| Re-ranking (Cohere), LlamaGuard, PII scrubbing                          | V2      | Quality / compliance polish        |
| Zendesk / Intercom native tickets                                       | V2      | Email + generic webhook is enough  |
| “Show me how” overlays, proactive chat, multi-step autonomous workflows | V2 / V3 | Extra agent UX                     |
| Notion / Confluence / Drive, multi-lingual embeddings                   | V3      | Extra ingestion                    |
| Pricing page, blog, changelog, SSO                                      | later   | Not required to prove the agent    |


---



## Current state (as of 2026-10-31)

Auth, workspaces, RBAC, the dashboard shell, knowledge ingestion, the tool registry, the API request engine, the internal chat orchestrator, the Knowledge and Tools screens, and sandbox chat are in place. The widget is not built yet. JS tools stay stored; the orchestrator does not emit `tool_js` or run them.

Known gap, fix before relying on the post-approve reply: Gemini 3.5 Flash Lite rejects the follow-up turn because the replayed function call has no thought signature. The HTTP tool still runs on approval. Rejection does not call the tool.

**Already in place**

- `[x]` FastAPI backend in `./backend` (users, login, JWT, password recovery)
- `[x]` React / Vite dashboard in `./frontend` (TanStack Router, shadcn/ui, Tailwind)
- `[x]` PostgreSQL + SQLModel + Alembic + pgvector
- `[x]` Public landing page at `/` (ember brand, HITL artifact, logged-in redirect to `/dashboard`)
- `[x]` `/signup`, `/login`, `/recover-password`, `/terms`, `/privacy`
- `[x]` Wordmark **Actionable AI** in chrome
- `[x]` Superuser admin (platform ops user CRUD — not client Admin)
- `[x]` Workspace RBAC (Admin / Editor / Viewer; invite, members, tenant-scoped product queries)
- `[x]` Frontend architecture Option A (dashboard stays; widget = `packages/widget` later)
- `[x]` Backend architecture Option B (modular monolith; `app/models/` package in place)

**Still template leftovers (must be replaced, not shipped as product)**

- `[ ]` Remove demo **Items** CRUD from dashboard and API (or hide it) once Knowledge / Tools exist
- `[x]` Replace template dashboard home with the Quick Start empty state
- `[x]` Hide Items from the sidebar (Phase 1.3) — Items API and `/dashboard/items` remain until Knowledge exists

---



## Path to MVP

Work in this order. Phase numbers stay as they are so older notes still point at the same work. **Build order changed 2026-10-30:** make chat usable inside the dashboard before building the embeddable widget. The widget channel, the host-page JS tool bridge (5.4), the snippet, and the widget preview (7.3) ship with Phase 6.

```text
1. Workspace + RBAC                         done
        ↓
2. Data plane (pgvector, Redis, tables)     done
        ↓
3.1–3.2 Knowledge ingestion API             done
        ↓
4.1 Tool registry APIs                      done
        ↓
4.2 API Request Engine                      done
        ↓
5. Chat orchestrator, internal channel only  done
        ↓
3.3 Knowledge screen  +  4.3 Tools screen    done
        ↓
7.1 Sandbox  +  7.2 Internal chat           done
        ↓
6. Embeddable widget  +  5.4 JS tools  +  7.3 preview  +  snippet  ← next
        ↓
8. Handoff + launch safety
        ↓
9. Integration docs
        ↓
10. QA and MVP acceptance
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
- `[x]` Add `workspace_id` on `User` as the **current** workspace pointer; Alembic migration; signup/service comes next
- `[x]` `CurrentWorkspace` dependency (from session user + active membership; never trust a client-supplied id without a membership check)
- `[x]` `app/services/` — signup does **not** auto-create a workspace (join-via-invite later). Optional `workspace_name` on signup, or `POST /workspaces/`, creates one and attaches the user as **Admin**. Each user may **create at most one** workspace and **join many** via invite.
- `[x]` `GET /api/v1/workspaces/me` — current workspace for the session
- `[x]` `GET /api/v1/workspaces/` — workspaces the user belongs to (`can_create` if they have not created one yet)
- `[x]` `PUT /api/v1/workspaces/current` — switch current workspace (must already be an active member)
- `[x]` `PATCH /api/v1/workspaces/me` — rename (Admin only)
- `[x]` All product queries filter by `workspace_id` from `CurrentWorkspace` (never trust a client-supplied workspace id without membership check)



### 1.2 Users inside a workspace (RBAC)

MVP roles (from PRD): **Admin**, **Editor**, **Viewer**.


| Role   | Can do                                                                          |
| ------ | ------------------------------------------------------------------------------- |
| Admin  | Billing-level: invite, change roles, workspace settings, all Editor powers      |
| Editor | Upload/delete docs, register/edit tools, use internal chat, copy widget snippet |
| Viewer | Read docs/tools, use internal chat, cannot mutate config                        |


- `[x]` `WorkspaceMembership` (`user_id`, `workspace_id`, `role`, `is_active`); `User.workspace_id` is current workspace only. Create at most one (`Workspace.created_by_id` unique); join many via invite. `GET /workspaces/` lists memberships; `PUT /workspaces/current` switches.
- `[x]` Replace template `is_superuser`-only gates for product routes with role checks
- `[x]` Keep platform `is_superuser` for *our* ops admin only (not client Admin)
- `[x]` Invite flow: Admin invites by email + role (pending until accepted or declined); invite email includes accept/decline links; new accounts set a password on the join page
- `[x]` List workspace members; Admin can change role or deactivate
- `[x]` Tests: cross-tenant isolation on members and items (knowledge/tools/chat inherit `CurrentWorkspace` when those APIs exist)



### 1.3 Dashboard shell for a real product

- `[x]` Sidebar: Dashboard (Quick Start), Knowledge, Tools, Chat (internal), Members — drop Items from nav
- `[x]` Empty-state home: “Name your workspace → upload a doc → ask a question”

---



## Phase 2 — Data plane for RAG and HITL

**Why now:** Ingestion and the agent both need vectors and a place to pause HITL state.

**Done when:** Postgres has pgvector, Redis is in Compose, and the schema in `02_Database_Schema.md` exists (including forward-looking `GithubRepository` with **no** sync logic).

### 2.1 PostgreSQL + pgvector

- `[x]` Enable `pgvector` on the app database (image `pgvector/pgvector:pg18`, extension in the migration)
- `[x]` Vector dimension: Gemini `gemini-embedding-2` at **1536** (normalized by the model), fixed in `app/core/embeddings.py` and settings
- `[x]` Add `Document` (`workspace_id`, `title`, `type` pdf/markdown/text, `status` processing/active/failed, `original_filename`, `error_message`, `created_at`)
- `[x]` Add `DocumentChunk` (`document_id`, `content`, `embedding` vector, `chunk_index`, optional `metadata` JSONB)
- `[x]` HNSW index on `embedding` with cosine ops (tune later)
- `[x]` Add `ToolRegistry` (`workspace_id`, `name` unique per workspace, `kind` http/js, `http_method`, `url`, `schema` JSONB, `requires_hitl`, `description`, `is_active`)
- `[x]` Add `GithubRepository` **table only** (`workspace_id`, `url`, `target_branch`, `last_sync`) — no OAuth, no workers
- `[x]` Alembic migration `b7e2a1c94d08` + model tests



### 2.2 Redis

- `[x]` Add Redis to `compose.yml` and `compose.deploy.yml` (ephemeral, Docker network only; local port 6380)
- `[x]` App settings: `REDIS_URL` (required outside development; Compose sets `redis://redis:6379/0`)
- `[ ]` Use Redis for: HITL pending-action state, SSE/pubsub if needed, and a **basic** rate-limit counter (Phase 8)
- `[x]` Health check pings Redis and returns 503 when it is down



### 2.3 Object / file storage for uploads

**Decided (2026-10-30):** Original files live on the VM boot volume. Staging and production each have about **80 GB** and no object storage. A Docker named volume on that disk holds the bytes (Docker’s data root is already there). Local Compose uses the same kind of volume. Do not add a separate block volume for MVP.

The disk is shared with the OS, images, and Postgres. Keep the **10MB** upload cap and prune unused images so the volume does not fill. A container recreate keeps the files; deleting the VM or the Docker volume does not. `pg_dump` does not include them — before the first real production client, the off-box backup must copy this directory too. Staging may still be wiped.

A later object store can replace the directory behind `services/knowledge/storage.py`. Routes must not assume a filesystem path.

- `[x]` Store: boot-volume disk on each VM (this section, deployment strategy §9, Oracle guide)
- `[x]` Persist original file bytes keyed by `document_id` (needed to re-process on failure)
- `[x]` Max size **10MB** to match the Knowledge UI spec (API contract said 50MB — implemented 10MB and updated the API contract)

---



## Phase 3 — Knowledge ingestion (RAG write path)

**Why now:** TTV is “upload → ask.” Nothing else matters until a file becomes searchable chunks.

**Done when:** Editor uploads a PDF or `.md`, status goes Processing → Active (or Failed), and chunks are queryable with cosine similarity.

### 3.1 Embedding + chunking pipeline

- `[x]` Config: `GEMINI_API_KEY`, embedding model `gemini-embedding-2`, chat model `gemini-3.5-flash-lite`
- `[x]` Extract text: Markdown as-is; PDF via a maintained extractor (fail the document if extract is empty)
- `[x]` Chunk with overlap (document chosen sizes, e.g. ~500–800 tokens, overlap ~10–20%)
- `[x]` Embed chunks; store in `DocumentChunk`
- `[x]` Run ingestion **asynchronously** (background task / worker) so the upload API returns immediately with `status: processing`
- `[x]` Idempotent re-process: replacing a document deletes old chunks then re-embeds
- `[x]` Duplicate filenames: auto-append timestamp (UI spec decision)
- `[x]` Input token / file safety: skip empty files; cap pages/chars so one upload cannot melt the worker



### 3.2 Knowledge APIs (dashboard)

Align with `03_MVP_API_Contracts.md`, plus list/status that the UI needs.

- `[x]` `POST /api/v1/knowledge/upload` — multipart, workspace from auth, returns `{ document_id, status: "processing" }`
- `[x]` `GET /api/v1/knowledge/documents` — list for the table (name, date, status)
- `[x]` `GET /api/v1/knowledge/documents/{id}` — detail + error message if failed
- `[x]` `DELETE /api/v1/knowledge/documents/{id}` — delete file + chunks
- `[x]` AuthZ: Editor+ to mutate; Viewer can list
- `[x]` Reject non-pdf / non-md / non-txt; reject > 10MB
- `[x]` Tests: upload happy path, isolation, invalid type, failed parse sets `failed`



### 3.3 Knowledge Base UI (dashboard)

Build this after the internal orchestrator (Phase 5), together with the Tools screen (4.3), and before sandbox chat (7.1). The upload API already exists.

Spec: `docs/4_Design_and_Prototyping/MVP/Dashboard/01_Quick_Start_and_Ingestion.md`

- `[x]` Route `/dashboard/knowledge`
- `[x]` Table: file name, date, status badges (Active / Processing / Failed)
- `[x]` Empty state + CTA “Upload Data”
- `[x]` Side panel: drag-and-drop, click to browse, determinate progress
- `[x]` Client-side type/size validation; toast on network interrupt
- `[x]` Multi-file upload in one drop
- `[x]` Poll (or lightweight SSE) so status flips without refresh
- `[x]` Failed row: tooltip with `error_message`
- `[x]` Keyboard + `sr-only` status text (spec §11)

---



## Phase 4 — Tool registry (give the agent hands)

**Why now:** The orchestrator must load a typed tool list per workspace. HITL flags live on the tool, not in the prompt.

**Done when:** An Editor can register an HTTPS (or localhost) endpoint with a JSON schema; POST/PUT/DELETE lock HITL on; the tool is available in sandbox chat.

### 4.1 Tool APIs

- `[x]` `POST /api/v1/tools/register` — body per API contract; force `requires_hitl=true` for POST/PUT/DELETE even if client sends false
- `[x]` `GET /api/v1/tools` — list
- `[x]` `GET /api/v1/tools/{id}`
- `[x]` `PATCH /api/v1/tools/{id}` — edit schema/url/description
- `[x]` `DELETE /api/v1/tools/{id}` (or deactivate)
- `[x]` Validate: `name` snake_case `^[a-z0-9_]+$`; unique per workspace (409)
- `[x]` Validate JSON Schema is an object with `type` / `properties`
- `[x]` Tool kinds for MVP:
  - **HTTP:** method + URL + schema (server-side execution via our API Request Engine)
  - **JS:** name + schema only (execution happens in the host page; we emit a tool-call event to the widget)
- `[x]` Tests: HITL hard-lock, 409 duplicate, Viewer cannot register



### 4.2 API Request Engine (server-side tools)

MVP needs real HTTP calls. Full SSRF hardening is V1; **do the minimum now** so we do not fetch metadata IPs.

- `[x]` HTTP client with timeouts
- `[x]` Block obvious SSRF: link-local, private RFC1918, and AWS/GCP metadata hosts (full SSRF hardening is V1). `localhost`, `127.0.0.1`, and `::1` stay allowed
- `[x]` HTTPS required except `localhost`, `127.0.0.1`, and `::1` for integrator testing
- `[x]` Pass through a caller-supplied bearer as `Authorization: Bearer` — we do not invent permissions. Internal chat passes the dashboard member’s token. The host end-user JWT arrives with Phase 6.
- `[x]` Map non-2xx to a structured error the LLM can explain (no fake success)
- `[x]` Simple retry: once on 502/503; no infinite loops



### 4.3 Tools & Actions UI (dashboard)

Build this after the internal orchestrator (Phase 5), together with the Knowledge screen (3.3), and before sandbox chat (7.1). The registry API already exists.

Spec: `docs/4_Design_and_Prototyping/MVP/Dashboard/02_Tool_Registration_Flow.md`

- `[x]` Route `/dashboard/tools`
- `[x]` Table: name, type (GET / JS / …), safety (Read only vs HITL)
- `[x]` Side panel: name, URL (HTTP), method, description, Monaco JSON schema editor
- `[x]` Changing method to POST/PUT/DELETE: HITL toggle ON and **disabled**
- `[x]` Save disabled on invalid JSON or invalid name
- `[x]` Unsaved-changes confirm when closing the panel
- `[x]` Duplicate-name inline error from 409

---



## Phase 5 — Chat orchestrator (the product brain)

**Why now:** Sandbox and `/dashboard/chat` need one streaming API. Build the `internal` channel here. Leave the widget channel and the host-page JS bridge (5.4) for Phase 6, after internal chat is usable.

**Done when:** A logged-in member can stream an answer from workspace documents, a write tool pauses for HITL, confirm runs the HTTP tool, and reject aborts. Widget auth is not part of this slice.

Specs: architecture §3.2, `03_MVP_API_Contracts.md`, `04_MVP_LLM_Prompts.md`.

### 5.1 Session and streaming API

- `[x]` `ChatSession` (or Redis-backed session) keyed by `session_id` + `workspace_id`
- `[x]` Persist messages enough to resume HITL and to attach a transcript on escalation
- `[x]` `POST /api/v1/chat/stream` — `text/event-stream` for channel `internal`
  - Request: `{ session_id, message, channel: "internal" }`
  - Events: `message` (token/text), `hitl_required`, `error`, `done`. Do not emit `tool_js` until 5.4.
- `[x]` `POST /api/v1/chat/hitl-confirm` — `{ pending_action_id, decision: "approved" | "rejected" }` streams the outcome or aborts
- `[ ]` Widget channel: require **host end-user JWT**, not the integrator’s dashboard JWT. Build this with Phase 6, not with the internal channel.
- `[x]` Internal/sandbox channel: require logged-in workspace member
- `[x]` Truncate user text (UI ~2000 chars; backend hard cap ~2000 tokens) **before** embed/LLM
- `[x]` Max tool iterations per turn (e.g. 5) so the graph cannot loop



### 5.2 RAG retrieval (read path)

- `[x]` Embed the query with the same model as ingestion
- `[x]` Top-k similarity search **scoped to workspace_id** (join through Document)
- `[x]` Only `status=active` documents
- `[x]` Wrap retrieved text in delimiters; system prompt: retrieved text is data, never instructions (cheap anti-injection for MVP)
- `[x]` If similarity is below a threshold, prefer “I don’t know” / handoff rather than guessing
- `[x]` Input token truncation of the *context pack* so the prompt cannot blow the model window



### 5.3 LangGraph agent

- `[x]` Graph nodes: retrieve → reason → tool or answer → (HITL interrupt) → execute → answer
- `[x]` Load workspace tools as LLM functions from `ToolRegistry`
- `[x]` Inject `request_hitl_approval` schema from `04_MVP_LLM_Prompts.md`
- `[x]` **Code-enforced** HITL: if tool `requires_hitl` and the model tries to call it directly, intercept and convert to HITL (do not trust the model)
- `[x]` On HITL: pause graph, store state in Redis under `pending_action_id`, emit `hitl_required` with **plain-language** title/summary only (no HTTP method, path, tool id, or “API”)
- `[x]` On approve: execute the HTTP tool through the API request engine and stream success or the structured error. JS tool events wait for 5.4.
- `[x]` On reject: stream “No problem, I won’t do that.”; do not retry the same write quietly
- `[x]` System prompt from `04_MVP_LLM_Prompts.md` (tune voice: customer widget vs internal dashboard)
- `[x]` Graceful LLM/provider errors → stable `error` SSE event



### 5.4 Client-side (JS) tools — with Phase 6

JS tools can already be stored. Host-page execution waits for the widget. Do not build this in the internal-channel slice. HTTP tools run through the Phase 4.2 engine.

- `[ ]` Registry entry has no URL; widget is told `{ name, arguments }`
- `[ ]` Widget looks up `window`/`registerTool` map; on missing/throw, show fallback text (do not crash)
- `[ ]` Writes still go through HITL **before** the widget invokes the JS function

---



## Phase 6 — Embeddable customer widget

**When:** After sandbox and internal chat (Phase 7.1 and 7.2) work. This is the surface beta clients ship on their own site. It consumes the Phase 5 orchestrator. Build the widget channel’s end-user JWT check and the JS tool bridge (5.4) here, plus the snippet (6.5) and the dashboard widget preview (7.3).

**Done when:** A host page loads one script, opens a Shadow DOM chat, streams answers, shows HITL in plain language, and confirms/rejects safely.

Spec: `docs/4_Design_and_Prototyping/MVP/Widget/01_Core_Chat_and_HITL_Flow.md`

### 6.1 Package and isolation

- `[ ]` New package `packages/widget` (Option A) — Vanilla JS or Preact, **not** the full dashboard React app; no import from `frontend/src` or `@/shared/ui`
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

**When:** Build 7.1 and 7.2 after the Knowledge and Tools screens, and before the widget. Internal time-to-value is signup → upload → sandbox question → HITL confirm. Copy-snippet and 7.3 wait for Phase 6.

**Done when:** A new Admin can upload a document, ask the sandbox a question, and confirm or reject a write tool without leaving the dashboard. Pasting a script tag is Phase 6, not this slice.

### 7.1 Quick Start + sandbox

Journey 1 in `User_Journeys.md`.

- `[x]` After first workspace: guided steps (upload → ask). Copy-snippet is Phase 6.5.
- `[x]` **Sandbox chat** on the dashboard using the internal orchestrator (`channel: internal`). This is dashboard UI, not the embeddable widget.
- `[x]` Redirect/focus sandbox when the first document becomes Active (target: usable within ~60s of upload)
- `[x]` Sandbox may use the dashboard user as identity; label it clearly as a test surface



### 7.2 Internal chatbot

PRD: internal chatbot is MVP (Marcus / sales-support).

- `[x]` Route `/dashboard/chat` — full-page chat, same APIs, workspace RAG + tools
- `[x]` Default to read-heavy behavior; still HITL if someone tests a write tool
- `[x]` Empty state if no documents: point to Knowledge upload



### 7.3 Widget preview — with Phase 6

Do not start this with sandbox chat. It mounts the real widget from Phase 6.

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
- `[x]` Minimum SSRF denylist on the API Request Engine (Phase 4.2)
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


| Sprint | Focus                                                                 | Exit                                                         |
| ------ | --------------------------------------------------------------------- | ------------------------------------------------------------ |
| **A0** | Phase 1.0: `app/models/` package split                                | **Done** — imports and tests green; DB schema unchanged     |
| **A**  | Phase 1–2: workspace, RBAC, pgvector, Redis, schema                   | **Done** — isolated tenants, product tables                 |
| **B**  | Phase 3.1–3.2: ingestion API                                          | **Done** — upload → Active chunks. Knowledge screen is C2   |
| **C1** | Phase 4.2 + Phase 5 internal channel                                  | **Done** — internal stream, HITL, and HTTP tool confirm     |
| **C2** | Phase 3.3 + 4.3: Knowledge and Tools screens                          | Upload and register from the dashboard                       |
| **C3** | Phase 7.1 + 7.2: sandbox and `/dashboard/chat`                        | **Done** — internal Q&A and HITL against a registered HTTP tool |
| **D**  | Phase 6 + 5.4 + 6.5 + 7.3: widget, JS tools, snippet, preview         | Script tag on an example host                               |
| **E**  | Phase 8–10: handoff, caps, tests, remove Items, beta dry-run          | MVP acceptance checklist all green                           |


---



## Definition of done — MVP

The MVP is done when **Phase 10.3** passes on a shared staging environment, not when individual tickets are closed. Marketing already says “live in minutes”; the implementation must match that sentence.
