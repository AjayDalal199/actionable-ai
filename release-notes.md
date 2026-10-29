# Release Notes

## Latest Changes

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
