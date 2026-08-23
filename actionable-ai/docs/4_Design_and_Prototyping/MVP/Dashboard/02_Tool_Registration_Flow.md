# UI/UX Specification: Agent Tool Registration Flow

## Document Metadata
- **Product:** Actionable AI (A²I) Platform
- **Feature:** Internal Dashboard (Tools & Actions Registry)
- **Version:** MVP (Phase 1)
- **Status:** Approved
- **Owner:** Product Team
- **Last Updated:** 2026-08-23

---

## 1. Feature Overview
### Purpose
To allow developers to register client-side JavaScript functions or backend API endpoints that the AI agent can execute.
### User Goal
Give the AI "hands" to perform actions, rather than just acting as a Q&A bot.
### Primary Users
Integrators (Developers).
### Entry Points
- Dashboard → Tools & Actions → "Register Tool" Button.
### Success Criteria
- Developer successfully defines a JSON schema for a tool.
- The tool appears in the Registry Table and is immediately available to the agent in the Sandbox.

---

## 2. User Flow
### Primary Flow (Registering an API Tool)
```text
[Click "Register Tool"]
    ↓
[Side Panel Opens with Configuration Form]
    ↓
[User enters Name: "cancel_subscription", Method: "DELETE"]
    ↓
[System auto-toggles "Requires HITL Confirmation" to ON and locks it]
    ↓
[User pastes JSON schema in the Monaco Editor]
    ↓
[User clicks Save]
    ↓
[Success Toast -> Tool added to Registry Table]
```

### Failure Flows
- **Invalid JSON Schema:** User types malformed JSON. The Monaco Editor highlights the syntax error in red. The "Save" button is disabled until fixed.
- **Naming Violation:** User names the tool `Cancel Subscription`. Frontend rejects it: "Tool names must be snake_case with no spaces."

---

## 4. Screen Specifications
## Screen: Tools & Actions Registry
### Purpose
Manage the agent's capabilities.
### Layout
```text
┌─────────────────────────────────────────┐
│ Breadcrumbs              [Register Tool]│
├─────────────────────────────────────────┤
│                                         │
│ Tool Name        Type        Safety     │
│ ─────────────────────────────────────── │
│ fetch_user       GET         [Read Only]│
│ cancel_sub       DELETE      [🛡️ HITL]  │
│                                         │
└─────────────────────────────────────────┘
```

---

## 6. Form Specifications
## Form: Tool Configuration Panel
### Fields
#### Tool Name
- **Type:** Text
- **Validation:** Must be valid `snake_case`. Regex: `/^[a-z0-9_]+$/`
- **Required:** Yes
#### Endpoint URL
- **Type:** URL
- **Validation:** Must be a valid `https://` URL (unless localhost for testing).
- **Required:** Yes
#### HTTP Method
- **Type:** Select Dropdown (GET, POST, PUT, DELETE)
- **Default:** GET
#### JSON Schema Editor
- **Type:** Monaco Code Editor Component
- **Validation:** Must parse as valid JSON.

---

## 8. Interaction Specifications
## Interaction: Security Safety Lock (HITL)
### Trigger
User changes the HTTP Method dropdown from `GET` to `DELETE`.
### Behavior
1. The toggle switch for "Requires Human-in-the-Loop Confirmation" automatically switches to the `ON` position.
2. The toggle becomes disabled (grayed out) so the user cannot turn it off.
3. A tooltip appears: "Destructive API methods (POST, PUT, DELETE) strictly require user confirmation for safety."

---

## 11. Accessibility
### Keyboard
- The Monaco editor traps focus. User must use `Esc` to break out of the code editor focus and tab to the "Save" button.

---

## 14. API / Backend Dependencies
## Register Tool
- **Method:** POST
- **Endpoint:** `/api/v1/tools/register`
- **Request:** `{ "name": "cancel_sub", "method": "DELETE", "url": "...", "schema": {...} }`
- **Response:** `201 Created`
- **Error behavior:** If name is already taken, returns 409 Conflict. Frontend displays inline error below the Tool Name field.

---

## 15. Edge Cases
- [x] **Duplicate Tool Name:** Handled via 409 API response.
- [x] **Unsaved Changes:** If user clicks outside the side-panel while editing, a Destructive Modal warns: "You have unsaved changes. Are you sure you want to discard them?"

---

## 20. Acceptance Criteria
## Feature
- [ ] Tool names strictly enforce snake_case.
- [ ] Monaco editor successfully validates JSON syntax before allowing save.
- [ ] Changing HTTP method to POST/PUT/DELETE explicitly locks the HITL toggle to ON.
- [ ] Unsaved changes warning triggers appropriately.
