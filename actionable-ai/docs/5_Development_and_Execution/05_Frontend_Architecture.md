# 05 Frontend Architecture

## Document Metadata

- **Product:** Actionable AI (A²I) Platform
- **Status:** Decided — Option A (2026-08-25)
- **Last Updated:** 2026-08-25
- **Companion:** [06 Backend Architecture](./06_Backend_Architecture.md), [01 System Architecture](./01_System_Architecture.md)

**Decision:** The dashboard stays in `frontend/` with the current layout. The embeddable widget will be a separate package (`packages/widget`), not built inside this React app. Rules in §7 are the working frontend architecture. Widget UI library (Preact vs vanilla) is deferred to Phase 6.

---

## 1. What this frontend must become

Two different products share a brand. They must **not** share a bundle.

| Surface | Who uses it | Constraints |
| --- | --- | --- |
| **Marketing + Dashboard** (`frontend/`) | Integrators, PMs, our ops admin | Full React app is fine. Auth, tables, Monaco, file upload. |
| **Embeddable widget** (does not exist yet) | End-users on *customer* sites | Tiny payload, Shadow DOM, no host CSS leakage, XSS sanitization, SSE. Vanilla JS or Preact. |

If the widget is built inside `frontend/src` with the dashboard’s React + Tailwind + shadcn stack, we will hit the Core Web Vitals risk in the P1 review. That is the main architectural line. Everything else is how we keep the dashboard from turning into a junk drawer.

---

## 2. Current stack (as of this review)

| Layer | Choice | Notes |
| --- | --- | --- |
| App | Vite 8 + React 19 + TypeScript | SPA. Production build is copied to `backend/app/frontend` and served by FastAPI. |
| Routing | TanStack Router (file-based) | `src/routes` → `routeTree.gen.ts`. Auto code-splitting is on. |
| Server state | TanStack Query | Query options live next to features. Route `loader`s prefetch. |
| HTTP | Generated Axios client (`@hey-api/openapi-ts`) | Regenerated from backend OpenAPI. Do not hand-edit `src/api`. |
| UI | Tailwind 4 + shadcn/ui (New York) | Components in `src/shared/ui`. Aliases in `components.json`. |
| Forms | react-hook-form + Zod | |
| Auth | JWT in `localStorage` (`access_token`) | 401/403 on Query/Mutation cache → clear token, hard redirect to `/login`. |
| Tests | Playwright | `frontend/tests`. Hits a running stack. |
| Package manager | Bun workspace | Root `package.json` workspaces: `frontend`, `packages/*`. |

Dev: Vite on `:5173` with `VITE_API_URL` pointing at FastAPI. Prod: same origin as the API.

---

## 3. Current folder structure

```text
frontend/
├── src/
│   ├── api/                 # GENERATED OpenAPI client. Do not edit.
│   ├── app/                 # QueryClient, React providers
│   ├── features/
│   │   ├── admin/           # Platform superuser user CRUD
│   │   ├── auth/            # session, login/signup mutations
│   │   ├── dashboard/       # shell: layout, sidebar, home
│   │   ├── items/           # TEMPLATE leftover
│   │   ├── marketing/       # public landing page
│   │   └── settings/        # account settings
│   ├── routes/              # URL map only (thin files)
│   ├── shared/
│   │   ├── components/      # Logo, DataTable, Error, Footer…
│   │   ├── hooks/
│   │   ├── lib/             # cn(), errors, theme
│   │   └── ui/              # shadcn primitives
│   ├── styles/              # global CSS tokens
│   ├── main.tsx
│   └── routeTree.gen.ts     # GENERATED
├── tests/                   # Playwright
├── openapi-ts.config.ts
└── components.json          # shadcn aliases → @/shared/*
```

### 3.1 How a screen is wired today

Example: Items (template), which is the pattern new dashboard pages should copy until we change it.

```text
URL  /dashboard/items
  →  routes/dashboard/items.tsx     createFileRoute, loader, <title>
  →  features/items/ItemsPage.tsx   UI
  →  features/items/queries.ts      queryOptions + ItemsService
  →  src/api  (generated)           HTTP
```

Route files stay thin: auth guard, loader, head, import the feature page. Layouts live in features (`DashboardLayout`, `AuthLayout`, `LegalLayout`).

This is already a **feature slice**, not “everything under `components/`”. That is worth keeping.

### 3.2 Routing map today

```text
/                      marketing landing (redirect to /dashboard if logged in)
/login  /signup  /recover-password  /reset-password
/terms  /privacy
/dashboard             shell (requires JWT)
/dashboard/            home greeting
/dashboard/items       template CRUD
/dashboard/admin       superuser only
/dashboard/settings
```

### 3.3 Strings, types, API, hooks — what we have vs what people expect

This is the usual mix-up: Angular/Nest (`services/`, `types/`), Redux (`store/`), and i18n libraries. Those folders are mostly **absent because the job is already done under other names**, not because the app is incomplete. One gap is real (copy is hardcoded). Nested `hooks/` / `components/` inside every feature is optional, not missing infrastructure.

#### Strings / i18n

**There is no i18n library.** No `react-i18next`, no locale files, no `t()`. Every user-visible string is a literal in the component (`"Items"`, landing copy arrays in `LandingPage.tsx`, Zod `message:` strings).

That is **English UI copy**, not “constants for multi-language.” Product multilingual *retrieval* (embeddings) is V3 and is a backend problem. Dashboard/widget translations are a separate product decision.

| Approach | When |
| --- | --- |
| Keep hardcoded English | MVP. Matches locked landing copy. Fast to ship. |
| Extract `messages.ts` per feature (still English) | Only if the same sentence is duplicated in many files. Not a translation system. |
| Real i18n (dictionaries + locale switch) | When we have a non-English buyer or the widget must speak the *host app’s* language. Not MVP. |

Do not add i18n “for architecture.” Empty locale trees become unmaintained copy.

#### Types (TypeScript)

We **do** have types. They are not in `features/foo/types.ts`.

| Kind | Where |
| --- | --- |
| API request/response (`UserPublic`, `ItemCreate`, …) | Generated in `src/api` from OpenAPI. Import `from "@/api"`. |
| Form shape | Zod schema next to the form; `z.infer<typeof formSchema>` is the type. |
| UI-only extras | Next to the file that needs them, e.g. `UserTableData` in `admin/columns.tsx`. |

A `types/` folder that re-exports OpenAPI types is duplication. Add a local `types.ts` only for types used by **several files in that feature** and **not** coming from the API.

#### API calling (“services”)

There is no `services/` folder **on purpose.**

```text
Component or queries.ts
  → UsersService / ItemsService / LoginService   (generated)
  → src/api  Axios client
  → FastAPI
```

Hand-written `src/services/userService.ts` that wraps Axios would fight the OpenAPI client. After backend changes we run `generate-client` and import the new service.

**Exception later:** SSE chat and upload progress may not fit the generated client. Those get a small module such as `features/chat/stream.ts`, not a global `services/` layer.

#### Hooks vs Query vs store

| Need | What we use | Where |
| --- | --- | --- |
| Server cache (list users, list items) | TanStack Query | `features/<name>/queries.ts` + `useQuery` / `useSuspenseQuery` / `useMutation` |
| Session token | Functions, not a store | `features/auth/session.ts` (`localStorage`) |
| “Current user” + login/logout | Feature hook | `features/auth/useAuth.ts` |
| Reusable UI hooks | React hooks | `shared/hooks/` (`useCustomToast`, `useMobile`, …) |
| Non-React helpers | Plain functions | `shared/lib/` (`cn`, `handleError`) |
| Global Redux/Zustand store | **None** | Server state is Query. UI state is `useState` in the component that owns it. |

`queries.ts` **is** the feature’s data-access file. Naming it `hooks/` or `services/` would be the same layer with a different label.

#### `shared/` vs `features/`

- `shared/ui` — shadcn primitives (Button, Dialog). No product meaning.
- `shared/components` — our composites used in many features (DataTable, Logo).
- `shared/hooks` and `shared/lib` — only if **two or more features** need them.
- `features/items/AddItem.tsx` — product UI. Do not move it to `shared` because it is a “component.”

### 3.4 Nested folders inside a feature

Today each feature is a **flat list of files** (`ItemsPage.tsx`, `AddItem.tsx`, `queries.ts`). That is correct while the folder has ~5–12 files.

The `hooks/`, `components/`, `utils/`, `store/`, `types/` tree inside *every* feature is a Vue/Angular habit. Empty subfolders are noise.

**Rule:** nest only when a single feature is hard to scan (roughly 12+ files or a clear cluster).

```text
features/knowledge/                 # when this exists and grows
  KnowledgePage.tsx
  queries.ts
  components/                       # only if many UI files
    UploadPanel.tsx
    DocumentTable.tsx
  lib/                              # optional: chunk status helpers
    status.ts
```

Still no `store/` unless we introduce client-only state that Query cannot hold (e.g. unsaved Monaco draft shared across panels). Still no `services/` — HTTP stays `@/api`.

### 3.5 Zustand, Context, and `useState` (do we need a store?)

**No Zustand for MVP.** We already have Context where it belongs. Local UI does not need a global store.

Zustand and Context solve the same class of problem: **client state that many distant components must read and write.** They are not a replacement for the API, and they are not required for a dialog’s open flag.

What this app actually uses today:

| State | Tool | Example |
| --- | --- | --- |
| Data from the server | TanStack Query | User list, current user, later documents/tools |
| Auth token | `localStorage` helpers | `features/auth/session.ts` |
| App-wide chrome | React Context | Theme (`ThemeProvider`), sidebar open (`SidebarProvider`) |
| One widget’s UI | `useState` in that component | Dialog open, FAQ accordion, password visibility |
| Forms | react-hook-form + Zod | Add item, signup, settings |
| Tables | TanStack Table | Column defs + row data from Query |

**Context we already have** is injection of a *capability* (theme, sidebar) around a large tree. That is the right use. Putting “current workspace documents” in Context would fight Query (two caches, no refetch, stale after upload).

**`useState` in the owner** is the right use for: sheet open, unsaved-changes prompt, which HITL card is confirming, composer text. The parent that renders the dialog owns `isOpen`. Children do not need a store to close it — pass `onClose` or keep state in the same file.

**Zustand** is worth it when all of this is true:

1. The data is **not** from the server (or is a ephemeral client overlay on top of it).
2. **Many unrelated routes/components** must read and write it.
3. Context would re-render a **wide** tree on every keystroke/update.

Possible later cases (not now): a multi-panel tool builder with unsaved schema shared between Monaco and a live preview on another part of the page; V2 “show me how” overlay state; a dashboard that mirrors widget session UI in two distant layouts. Internal chat can keep messages in the chat feature (`useState` + SSE buffer, or Query once we persist sessions). Workspace membership is Query (`GET /workspaces/me`), not a store.

**Do not** add Zustand “so we have a store folder.” That recreates Redux ceremony for `setIsOpen(true)`.

Prop drilling is **passing a value through components that do not use it** so a descendant can. That is not the same as “a child received a prop.” `DeleteUser` taking `id` is the row’s input. `ItemsPage` passing `items` through `Layout → Main → Table → Row → Cell` would be drilling.

This app avoids that without Zustand:

1. **Read data where it is needed.** `AppSidebar` calls `useAuth()` itself. `DashboardLayout` does not pass `user` down. TanStack Query is a cache: two `useQuery` with the same key are one request, not two trees to thread through.
2. **Keep UI state in the widget that owns it.** `AddItem` holds `isOpen`. The page does not know the dialog exists.
3. **Pass props one level when they are real inputs.** Column → `DeleteUser id={user.id}` is normal. If you ever have three unused wrappers, use Context for *that* slice (we already do for theme/sidebar), not a global store.

A dashboard page is usually 2–3 components deep. Zustand does not get rid of props; it hides them behind `useStore()`, which is the same coupling with worse stack traces.

---

## 4. What will pressure this layout

From the MVP task list, the dashboard will grow these slices:

- `workspace` — current tenant, rename, members
- `knowledge` — upload, document table, status polling
- `tools` — registry table, Monaco schema editor
- `chat` — internal / sandbox chat (SSE, HITL cards)
- `integration` — script snippet, JWT minting docs
- `handoff` — workspace support email / webhook settings

Plus a **widget** that cannot live here.

If we dump all of that into `features/` with no rules, we will still be fine for a while. The real bottlenecks are elsewhere.

---

## 5. Bottlenecks if we keep going unchanged

| Risk | Why it happens | When it hurts |
| --- | --- | --- |
| **Widget inside this app** | Dashboard deps (React 19, Radix, Tailwind) ship to every customer page | First widget spike |
| **Generated client used for SSE** | OpenAPI client is Axios request/response. Chat is a long-lived `text/event-stream` | Phase 5 chat |
| **No workspace in client state** | Auth is “a user + a token”. Product is “a user in a tenant” | Phase 1 APIs land |
| **Monaco / PDF / markdown in the main chunk** | Tool form and chat markdown will pull heavy libs unless they are route-split | Tools + chat pages |
| **localStorage JWT** | XSS on our own origin can steal the dashboard token. Acceptable for MVP; not for enterprise | V2 |
| **Marketing + app one SPA** | Fine at our size. Landing JS still downloads dashboard vendor unless we split well | Already mitigated somewhat by TanStack code splitting |
| **`features/items` as the mental model** | People copy owner-scoped CRUD instead of workspace-scoped CRUD | Every new screen |

None of these require rewriting the dashboard. They require **rules** and **one extra package**.

---

## 6. Options

### Option A — Keep this app as the dashboard; widget is a separate package — **chosen**

**Idea:** Do not restructure `frontend/src`. Keep thin routes + features + shared. Add `packages/widget` (Vanilla JS or Preact, own Vite build, Shadow DOM, own CSS). Optionally add `packages/widget` to the Bun workspace like `packages/react-email`.

```text
packages/
  react-email/     already exists
  widget/          NEW — embeddable Web Component, published or CDN’d
frontend/          marketing + authenticated dashboard only
```

**Fits:** MVP, V1, and a small team. Matches system architecture (“unified frontend” + “embeddable widget”).

**Cost:** Two build pipelines. Dashboard cannot reuse widget internals (and should not). Chat UI will be implemented twice at a glance (sandbox vs widget) unless we extract a *tiny* headless chat client later.

**Does not fix:** Backend coupling, SSE client, workspace context — those are add-ons inside this option.

### Option B — Full Feature-Sliced Design (FSD)

Split `src` into `app` / `pages` / `widgets` / `features` / `entities` / `shared` with strict import rules.

**Fits:** Very large frontend teams.

**Cost:** We would rename almost every file before writing Knowledge. Layers like `entities/document` are empty until APIs exist. High ceremony, low payoff at our size.

**Verdict:** Overkill. Option A already has features + shared.

### Option C — Colocate everything under `routes/`

```text
routes/dashboard/knowledge/
  index.tsx
  KnowledgeTable.tsx
  UploadPanel.tsx
  queries.ts
```

**Fits:** People who want “open the URL, see the code.”

**Cost:** Cross-route reuse (HITL card in sandbox *and* internal chat) gets messy. We already split routes vs features on purpose.

**Verdict:** Worse than A for HITL/chat, which will appear on more than one URL.

### Option D — Multiple frontend apps (marketing, dashboard, widget)

```text
apps/web/          Next.js marketing
apps/dashboard/    Vite dashboard
packages/widget/
```

**Fits:** Separate deploy, separate teams, SEO-heavy marketing.

**Cost:** Three toolchains, shared auth cookies across origins, duplicate design tokens. Marketing is already a static-ish page inside the SPA and that is enough for MVP.

**Verdict:** Defer. SEO can be a later extract. Do not start here.

### Option E — Replace Vite/TanStack with Next.js

**Fits:** If we wanted RSC, file-system server routes, or hosting on Vercel as the core app.

**Cost:** We already have FastAPI as the API and static host. Next.js would duplicate backend concerns or force BFF complexity. Widget still cannot be a Next app.

**Verdict:** No. Stay on Vite for the dashboard.

---

## 7. Working architecture (Option A)

These rules are **in force**. Change them only with an explicit architecture update.

1. **Dashboard stays in `frontend/`** with the current layout: `routes` (URLs) → `features` (product UI) → `shared` (design system) → `api` (generated).
2. **Widget is `packages/widget`**, own entry, own bundle, Shadow DOM, no import from `frontend/src` or `@/shared/ui`.
3. **New dashboard work is a new feature folder**, not more files in `dashboard/` or `shared/components`.
   - `features/workspace`, `features/knowledge`, `features/tools`, `features/chat`, …
4. **Route files stay under ~40 lines.** If a route file grows UI, the UI is in the wrong place.
5. **Talk to the API only through generated services**, except SSE (and upload progress XHR if the generated client cannot stream progress). Put those exceptions in `features/chat/stream.ts` (or similar), not in random components.
6. **Workspace is client context**, not a global later. After Phase 1 APIs exist: Query for `GET /workspaces/me`, pass workspace id into feature query keys. Do not trust a workspace id from the URL without the server also checking membership.
7. **Heavy editors are dynamic imports** (Monaco, markdown preview) so they do not sit on `/dashboard`.
8. **Do not share shadcn with the widget.** Host CSS isolation is the product. A shared component library would fight Shadow DOM and inflate the widget.

### 7.1 Target dashboard folders (when features exist)

```text
frontend/src/features/
  admin/          keep — platform ops, not client Admin
  auth/
  dashboard/      shell only (layout, sidebar, home empty-state)
  workspace/      members, rename — Phase 1
  knowledge/      Phase 3 UI
  tools/          Phase 4 UI
  chat/           sandbox + internal chat — Phase 5/7
  settings/       keep
  marketing/      keep
  items/          delete when Knowledge exists (not a blocker for architecture)
```

### 7.2 Widget package (when we reach Phase 6)

```text
packages/widget/
  src/
    index.ts              custom element definition
    shadow.ts             attach shadow root, inject CSS
    chat/                 composer, feed, HITL card
    sse.ts                EventSource / fetch stream
    tools.ts              A2I.registerTool
  vite.config.ts          library / IIFE build for <script src>
```

Public API should be boring: one script, attributes or `init({ workspace, token })`, `registerTool(name, fn)`.

---

## 8. Decision log

| # | Decision | Status | Choice |
| --- | --- | --- | --- |
| F1 | Dashboard structure | **Decided** | Option A — keep `routes` + `features` + `shared` + generated `api` |
| F2 | Widget location | **Decided** | `packages/widget` (own bundle, Shadow DOM). Do not put it in `frontend/src` |
| F3 | Widget UI library | Deferred to Phase 6 | Preact or vanilla. Never full React + shadcn |
| F4 | Sandbox chat vs embed widget | Deferred to Phase 6–7 | Prefer embedding the widget in sandbox if JWT allows; else a thin stream helper |
| F5 | SSE client | **Decided** | `fetch` + `ReadableStream` (POST `/chat/stream`). Not `EventSource` |
| F6 | Dashboard auth storage | **Decided** | `localStorage` for MVP; httpOnly cookie is V2 |
| F7 | Design tokens | **Decided** | One ember/zinc token file for marketing + dashboard only |
| F8 | UI language | **Decided** | Hardcoded English for MVP. No i18n library |
| F9 | Feature subfolders | **Decided** | Flat until a feature is hard to scan (~12+ files); then nest |
| F10 | Client store | **Decided** | No Zustand. `useState` + existing Context + TanStack Query |

---

## 9. What not to do in the next slice

- Do not rewrite the folder tree as part of Workspace.
- Do not add Next.js, Redux, or a second CSS framework.
- Do not put Knowledge/Tools routes in until those APIs exist (empty nav is fine).
- Do not start the widget package until chat streaming exists on the backend.

The first frontend change that *is* architecture-aligned, when we get there: feature `workspace` + query for `/workspaces/me`, still using this folder layout.
