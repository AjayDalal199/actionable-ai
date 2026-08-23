# UI/UX Specification: Quick Start & Data Ingestion Flow

## Document Metadata
- **Product:** Actionable AI (A²I) Platform
- **Feature:** Internal Dashboard (Knowledge Base Upload)
- **Version:** MVP (Phase 1)
- **Status:** Approved
- **Owner:** Product Team
- **Last Updated:** 2026-08-23

---

## 1. Feature Overview
### Purpose
Allows clients to upload PDFs and Markdown files to train the AI's RAG knowledge base.
### User Goal
Upload existing API documentation so the chatbot can answer technical questions immediately.
### Primary Users
Integrators (Developers) and Content Curators (PMs).
### Entry Points
- Dashboard → Knowledge Base → "Upload Data" Button.
### Success Criteria
- User uploads a file.
- The file is chunked, embedded, and displayed as "Active" in the Document Registry table.

---

## 2. User Flow
### Primary Flow (File Upload)
```text
[Click "Upload Data"]
    ↓
[Side Panel Opens with Drag-and-Drop Zone]
    ↓
[User drops a 2MB PDF file]
    ↓
[Frontend validates size/type -> Shows Uploading Progress Bar]
    ↓
[Upload completes -> File appears in Table as "Processing" (Yellow)]
    ↓
[Backend finishes embedding -> Status changes to "Active" (Green)]
```

### Failure Flows
- **Validation Failure:** User uploads a `.docx` file. Frontend immediately rejects: "Unsupported file type. Only PDF and Markdown are supported for MVP."
- **Size Limit Failure:** User uploads 25MB PDF. Frontend rejects: "File exceeds 10MB limit."
- **Processing Error:** Backend fails to parse text. Status badge in table turns Red (`Failed`). Hover tooltip explains why.

---

## 4. Screen Specifications
## Screen: Knowledge Base
### Purpose
Manage all data sources feeding the RAG pipeline.
### Layout
```text
┌─────────────────────────────────────────┐
│ Breadcrumbs                [Upload Data]│
├─────────────────────────────────────────┤
│                                         │
│ File Name       Date         Status     │
│ ─────────────────────────────────────── │
│ api_docs.pdf    Aug 23       [🟢 Active]│
│ faq.md          Aug 23       [🟡 Process]│
│                                         │
└─────────────────────────────────────────┘
```

---

## 5. Component Specifications
## Component: Upload Drag-and-Drop Zone
### Purpose
Frictionless file uploading.
### Behavior
- **Default:** Dashed border, light gray background. Text: "Drag and drop files here, or click to browse."
- **Drag Over:** Border turns solid Primary Color, background slightly tints. Text changes to "Drop to upload."
- **Uploading:** Displays a determinate progress bar (0-100%).

---

## 7. UI States
## Empty State (Document Table)
**Condition:** Workspace has 0 uploaded documents.
**Message:** "Your AI has no knowledge yet. Upload your first document to get started."
**CTA:** Large `[Upload Data]` button centered in the table body.

## 11. Accessibility
### Keyboard
- The "Upload Data" button is focusable via `Tab`.
- The Drag-and-Drop zone is clickable via `Enter` to open the native OS file picker.
### Screen Readers
- The table uses semantic `<th>` and `<td>` tags. Status badges use hidden screen-reader text (e.g., `<span class="sr-only">Status: </span>Active`).

---

## 14. API / Backend Dependencies
## Upload Document
- **Method:** POST
- **Endpoint:** `/api/v1/knowledge/upload`
- **Request:** `multipart/form-data` (file blob).
- **Response:** `{ "document_id": "uuid", "status": "processing" }`
- **Loading behavior:** Frontend shows determinate progress bar based on XMLHttpRequest `progress` event.

---

## 15. Edge Cases
- [x] **Network failure mid-upload:** Show toast error "Upload interrupted. Please try again."
- [x] **Duplicate filename:** Backend appends a timestamp to prevent overwrites, or frontend warns user. (Decision: Auto-append timestamp for MVP).

---

## 20. Acceptance Criteria
## Feature
- [ ] User can upload multiple files at once.
- [ ] Table updates status asynchronously without requiring a page refresh (polling or WebSockets).
- [ ] Empty state renders correctly.
- [ ] Invalid file types are blocked client-side.
