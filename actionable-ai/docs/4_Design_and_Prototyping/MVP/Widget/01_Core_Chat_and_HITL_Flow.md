# UI/UX Specification: Widget Core Chat & HITL Flow

## Document Metadata
- **Product:** Actionable AI (A²I) Platform
- **Feature:** Embeddable Widget (Core Chat & Human-in-the-Loop)
- **Version:** MVP (Phase 1)
- **Status:** Approved
- **Owner:** Product Team
- **Last Updated:** 2026-08-23

---

## 1. Feature Overview
### Purpose
To provide an embeddable, floating chat interface that allows end-users to query documentation and safely execute client-side or backend actions on their behalf.
### User Goal
Get immediate answers or have a task completed without navigating the host application manually.
### Primary Users
End-Users of the client's SaaS platform.
### Entry Points
- Floating Action Button (FAB) on the bottom right of any client webpage.
### Success Criteria
- User receives an accurate RAG answer OR successfully executes a registered tool.
- The UI never hangs or appears frozen during the 3-8s LLM generation window.

---

## 2. User Flow
### Primary Flow (Agentic Action)
```text
[Click Widget Launcher]
    ↓
[Type "Cancel my subscription" -> Hit Send]
    ↓
[Widget instantly shows Pulsing 3-dot Loader (Optimistic UI)]
    ↓
[Backend resolves intent to `cancel_sub` tool (Write Action)]
    ↓
[Widget replaces loader with HITL Confirmation Card]
    ↓
[User clicks "Confirm"]
    ↓
[Widget shows Success Toast and AI success message]
```

### Failure Flows
- **API Timeout:** Widget removes loader, displays "I'm having trouble connecting to my brain right now. Please try again."
- **HITL Cancelled:** User clicks Cancel. AI responds: "No problem, I've aborted that action."

---

## 3. Information Architecture
### Navigation
```text
[Client Website]
└── [Widget FAB]
    └── [Chat Modal (Single Feed)]
```

---

## 4. Screen Specifications
## Screen: Main Chat Feed
### Purpose
The sole interface for interacting with the AI.
### Layout
```text
┌─────────────────────────────────────────┐
│ Header: [Agent Name]             [Close]│
├─────────────────────────────────────────┤
│                                         │
│ [AI Bubble: Hello! How can I help?]     │
│                                         │
│                    [User Bubble: Hi!]   │
│                                         │
├─────────────────────────────────────────┤
│ [Type a message...]             [Send]  │
└─────────────────────────────────────────┘
```

### Components
#### HITL Confirmation Card
- **Type:** Inline Card within Message Feed
- **Purpose:** Securely request permission before a destructive action.
- **Content:** Warning Icon, Action Title, Action Description, Confirm/Cancel Buttons.
- **Primary action:** `Confirm` (Sends execution signal via SSE).
- **Secondary actions:** `Cancel` (Aborts action).

---

## 5. Component Specifications
## Component: Optimistic Loader
### Purpose
Mask the high latency of LLM API calls.
### Content
A small chat bubble containing 3 horizontally bouncing dots.
### Behavior
Appears the *millisecond* the user hits send. Disappears the moment the first Server-Sent Event (SSE) chunk is received from the backend.

---

## 6. Form Specifications
## Form: Composer Input
### Fields
#### Message Input
- **Type:** Textarea (auto-expanding up to 4 lines)
- **Placeholder:** "Ask me anything or ask me to do something..."
- **Required:** Yes
- **Submit behavior:** Hitting `Enter` (without Shift) triggers submit. Clears input, disables input, appends user message to feed, and triggers Optimistic Loader.

---

## 7. UI States
## Default
Launcher button is visible. Modal is hidden.
## Loading
**Condition:** User submitted a message.
**Behavior:** Composer input disabled. Send button disabled. Pulsing loader bubble appended to feed.
## Error
**Condition:** SSE connection drops or LLM returns 500.
**Message:** "Connection lost. Please try again."

---

## 8. Interaction Specifications
## Interaction: Closing the Widget
### Trigger
User clicks the `X` icon in the header or clicks the background overlay (on mobile).
### Behavior
1. CSS `transform: translateY(20px)` and `opacity: 0` is applied.
2. After 300ms transition, `display: none` is set.
### Result
Widget is hidden but state (chat history) is preserved in memory for the session.

---

## 10. Responsive Behavior
## Desktop
- Fixed dimensions (e.g., `380px` wide, `700px` max-height).
- Attached to bottom-right corner with `20px` margins.
## Mobile
- `width: 100vw`, `height: 100vh`.
- Margin `0`. Border-radius `0`. Header takes up top safe-area.

---

## 11. Accessibility
### Keyboard
- User can `Tab` directly to the Composer input when the widget opens.
- `Enter` submits the form.
### Screen Readers
- The chat feed uses `role="log"` and `aria-live="polite"` so screen readers announce new AI messages automatically.
- HITL Card uses `aria-live="assertive"` as it requires immediate user attention.

---

## 13. Data Requirements
### Data Formatting
- AI text responses must be parsed using a secure Markdown-to-HTML library (e.g., `marked` + `DOMPurify`).

---

## 14. API / Backend Dependencies
## Stream Chat
- **Method:** POST
- **Endpoint:** `/api/v1/chat/stream`
- **Request:** `{ "session_id": "uuid", "message": "string" }`
- **Response:** Server-Sent Events (SSE) streaming Markdown and JSON tool-call signals.
- **Permission requirement:** Valid JWT from the host application.

---

## 15. Edge Cases
- [x] **Very long text:** User pastes 10,000 words. Frontend truncates input to max length (e.g., 2000 chars) before sending.
- [x] **CSS Leakage:** Host website sets `button { background: red !important; }`. Widget uses Shadow DOM to remain completely unaffected.

---

## 18. Design Decisions
## Decision: Using Shadow DOM
### Question
How do we prevent our widget from inheriting bad CSS from 1,000 different client websites?
### Decision
Wrap the entire React/Preact tree inside a Web Component Shadow Root.
### Reason
It guarantees 100% CSS isolation without having to write aggressive reset styles for every single HTML element.

---

## 20. Acceptance Criteria
## Feature
- [ ] User can open and close the widget.
- [ ] Optimistic loader appears instantly upon sending a message.
- [ ] HITL Card renders correctly when a "Write" tool is triggered.
- [ ] Clicking Confirm/Cancel on the HITL card disables the buttons permanently for that specific card.
- [ ] Widget is fully responsive and takes over the screen on mobile devices.
