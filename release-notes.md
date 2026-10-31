# Release Notes

## Latest Changes

### Features

* Embed a customer widget from one script. End users stream answers in a Shadow DOM chat and confirm writes in plain language. JavaScript tools run on the host page.
* Let members ask from uploaded documents in dashboard chat, with replies streaming as markdown, and confirm write tools before they run.
* Let editors upload documents and register HTTP tools. Write methods always pause for confirmation.
* Ingest uploads in the background and embed them with Gemini.

### Fixes

* Keep a single CORS origin on widget responses so the dashboard preview can stream.
* Retry Gemini when the model is overloaded, and forward the API key and chat model on deploy.
* Keep chat session ids working when the page is served over plain HTTP.
* Fail the health check when Redis is unreachable.

### Internal

* Add pgvector tables for documents, tools, and repositories.

## 0.1.1 (2026-10-29)

### Features

* Deploy staging at `staging.dactionlabs.com` and production at `app.dactionlabs.com` as separate Docker Compose stacks on Oracle Cloud.
* Deploy staging from `develop`, and production only when a release pull request merges into `master`.
* Keep Adminer on staging. Production does not expose it.

### Fixes

* Run the API with one worker so the 6 GB VMs do not run out of memory during normal operation.

### Docs

* Document the Oracle Cloud bootstrap, GitHub Environments, and how a release promotes staging to production.

### Internal

* Bump frontend, backend, and GitHub Actions dependencies, keeping TypeScript 5.9 and React Table v8.
* Disable the FastAPI Cloud deploy workflow so a push to `master` cannot deploy there.

## 0.1.0 (2026-10-01)

First Actionable AI product snapshot (Phase 1: workspaces and RBAC). Knowledge, tools, chat, and the embeddable widget are not in this release.

### Features

* Add the public marketing landing page, plus `/terms` and `/privacy`.
* Add the dashboard shell with Quick Start empty state and product sidebar.
* Add workspaces: create, switch current workspace, and rename.
* Add workspace RBAC (Admin, Editor, Viewer), member management, and email invitations.

### Fixes

* Log users in after signup and send them to the dashboard.

### Refactors

* Split SQLModel tables into an `app.models` package.

### Docs

* Lock frontend Option A and backend Option B architecture.
* Document Compose staging/production deployment and software licensing.
