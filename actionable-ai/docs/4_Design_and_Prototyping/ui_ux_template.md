# UI/UX Specification Template

## Document Metadata

- **Product:** [Product Name]
- **Feature:** [Feature Name]
- **Version:** [Version]
- **Status:** Draft / In Review / Approved
- **Owner:** [Name / Team]
- **Last Updated:** [Date]

---

## 1. Feature Overview

### Purpose

[What problem does this feature solve?]

### User Goal

[What does the user want to accomplish?]

### Primary Users

[Who uses this feature?]

### Entry Points

- [Where can the user enter this feature?]
- [Example: Dashboard → Projects → Create Project]

### Success Criteria

- [What does successful completion look like?]

---

## 2. User Flow

### Primary Flow

```text
[Entry Point]
    ↓
[Step 1]
    ↓
[Step 2]
    ↓
[Step 3]
    ↓
[Success State]
```

### Alternative Flows

#### Flow: [Name]

```text
[Trigger]
    ↓
[Condition]
    ↓
[Alternative outcome]
```

### Failure Flows

- [Validation failure]
- [Network/API failure]
- [Permission failure]
- [Session expiration]
- [Other failure]

---

## 3. Information Architecture

### Navigation

```text
[Application]
├── [Section]
│   ├── [Page]
│   └── [Page]
├── [Section]
└── [Section]
```

### Page Hierarchy

```text
[Feature]
├── [List]
├── [Create]
├── [Details]
│   ├── [Tab]
│   └── [Tab]
└── [Settings]
```

---

# 4. Screen Specifications

Repeat this section for every screen.

## Screen: [Screen Name]

### Purpose

[Why does this screen exist?]

### Route

`/[route]`

### Entry Points

- [Entry point]
- [Entry point]

### Exit Points

- [Destination]
- [Destination]

### Layout

```text
┌─────────────────────────────────────────┐
│ Header                                  │
├─────────────────────────────────────────┤
│ Page title                 Primary CTA  │
├─────────────────────────────────────────┤
│ Toolbar / Filters                       │
├─────────────────────────────────────────┤
│                                         │
│ Main Content                             │
│                                         │
└─────────────────────────────────────────┘
```

### Components

#### [Component Name]

- **Type:** [Button / Input / Table / Card / Modal / etc.]
- **Purpose:** [Purpose]
- **Content:** [What it displays]
- **Primary action:** [Action]
- **Secondary actions:** [Actions]
- **Navigation:** [Destination]
- **Visibility:** [When it is shown]
- **Permissions:** [Who can use it]

---

# 5. Component Specifications

## Component: [Component Name]

### Purpose

[Why does this component exist?]

### Content

[What information does it display?]

### Actions

- [Action 1]
- [Action 2]

### Behavior

[What happens when the user interacts with it?]

### Validation

- [Rule 1]
- [Rule 2]

### Permissions

- [Role / permission]

### Navigation

- [Destination]

### Dependencies

- [Data / component / API dependency]

---

# 6. Form Specifications

## Form: [Form Name]

### Fields

#### [Field Name]

- **Type:** [Text / Number / Select / Date / etc.]
- **Label:** [Label]
- **Placeholder:** [Placeholder]
- **Required:** Yes / No
- **Default:** [Default value]
- **Validation:** [Rules]
- **Help text:** [Optional help text]

### Validation Errors

| Condition | Message |
|---|---|
| [Condition] | [Error message] |
| [Condition] | [Error message] |

### Form Actions

- **Primary:** [Action]
- **Secondary:** [Action]
- **Cancel behavior:** [What happens]
- **Submit behavior:** [What happens]

---

# 7. UI States

Every important screen and component should define its states.

## Default

[Normal state]

## Loading

**Condition:** [When loading occurs]

**Behavior:**
- [What is shown]
- [What is disabled]
- [Whether skeletons/spinners are used]

## Empty

**Condition:** [When there is no data]

**Message:** [Message]

**CTA:** [Action]

## No Results

**Condition:** [Search/filter returns no results]

**Message:** [Message]

**Action:** [Clear search / reset filters]

## Error

**Condition:** [When error occurs]

**Message:** [Message]

**Action:** [Retry / go back / contact support]

## Success

**Condition:** [Successful operation]

**Feedback:** [Toast / banner / redirect / inline message]

## Disabled

**Condition:** [When component is unavailable]

**Reason:** [Why]

## Permission Restricted

**Condition:** [When user lacks permission]

**Behavior:** Hide / Disable / Show explanation

---

# 8. Interaction Specifications

## Interaction: [Interaction Name]

### Trigger

[User action]

### Preconditions

[What must be true before the interaction]

### Behavior

1. [Step]
2. [Step]
3. [Step]

### Feedback

[Toast / inline message / modal / loading state]

### Result

[Final state]

### Failure Behavior

[What happens if the operation fails]

---

# 9. Navigation

### Navigation Rules

| From | Action | Destination |
|---|---|---|
| [Screen] | [Action] | [Screen] |
| [Screen] | [Action] | [Screen] |

### Back Behavior

[Describe browser/back button behavior.]

### Unsaved Changes

[What happens when the user leaves with unsaved changes?]

---

# 10. Responsive Behavior

## Desktop

[Layout and behavior]

## Tablet

[Layout and behavior]

## Mobile

[Layout and behavior]

### Breakpoint-Specific Changes

- [Component that changes]
- [Navigation behavior]
- [Table/card behavior]
- [Modal behavior]

---

# 11. Accessibility

### Keyboard

- [Keyboard requirements]
- [Tab order]
- [Keyboard shortcuts]
- [Escape behavior]

### Screen Readers

- [Accessible labels]
- [Announcements]
- [Semantic requirements]

### Visual

- [Contrast requirements]
- [Focus indicators]
- [Do not rely solely on color]
- [Text scaling requirements]

---

# 12. Permissions & Roles

| Element / Action | Admin | Manager | Employee | Other |
|---|---:|---:|---:|---:|
| View | ✓ | ✓ | ✓ | [ ] |
| Create | ✓ | ✓ | ✗ | [ ] |
| Edit | ✓ | ✓ | [ ] | [ ] |
| Delete | ✓ | ✗ | ✗ | [ ] |

### Unauthorized Behavior

[Hide / disable / show explanation / redirect]

---

# 13. Data Requirements

### Data Required by Screen

| Data | Source | Required | Purpose |
|---|---|---:|---|
| [Field] | [API / local / derived] | Yes | [Purpose] |
| [Field] | [API / local / derived] | No | [Purpose] |

### Data Formatting

- **Dates:** [Format]
- **Currency:** [Format]
- **Numbers:** [Format]
- **Names:** [Format]
- **Empty values:** [Display behavior]

---

# 14. API / Backend Dependencies

This section describes what the UI needs from the backend without becoming a full technical specification.

## [Operation Name]

- **Method:** GET / POST / PUT / PATCH / DELETE
- **Endpoint:** `/api/[endpoint]`
- **Request:** [Fields]
- **Response:** [Fields]
- **Loading behavior:** [Behavior]
- **Error behavior:** [Behavior]
- **Permission requirement:** [Permission]

---

# 15. Edge Cases

Consider unusual but realistic situations.

- [ ] Very long text
- [ ] Missing data
- [ ] Large dataset
- [ ] No results
- [ ] Network failure
- [ ] API timeout
- [ ] Session expiration
- [ ] Permission changes
- [ ] Concurrent edits
- [ ] Deleted resource
- [ ] Duplicate submission
- [ ] Browser refresh
- [ ] Unexpected server response

### Additional Edge Cases

[Add feature-specific cases.]

---

# 16. Feedback & Notifications

## Success

- **Trigger:** [Condition]
- **Message:** [Message]
- **Type:** Toast / Banner / Inline / Modal
- **Duration:** [Duration]

## Error

- **Trigger:** [Condition]
- **Message:** [Message]
- **Type:** Toast / Banner / Inline / Modal
- **Recovery:** [Action]

## Confirmation

- **Trigger:** [Condition]
- **Message:** [Message]
- **Actions:** [Cancel / Confirm]

---

# 17. Analytics & Tracking

Define meaningful user actions that should be tracked.

| Event | Trigger | Properties |
|---|---|---|
| `[event_name]` | [Trigger] | [Properties] |
| `[event_name]` | [Trigger] | [Properties] |

### Important Metrics

- [Conversion]
- [Completion rate]
- [Drop-off]
- [Feature usage]
- [Error rate]

---

# 18. Design Decisions

Record decisions that designers and developers should not reinterpret without discussion.

## Decision: [Title]

### Question

[Question being decided]

### Decision

[Chosen approach]

### Reason

[Why this approach was selected]

### Alternatives Considered

- [Alternative]
- [Alternative]

---

# 19. Open Questions

- [ ] [Question]
- [ ] [Question]
- [ ] [Question]

### Decision Owner

[Person / Team responsible]

---

# 20. Acceptance Criteria

## Screen: [Screen Name]

- [ ] Screen can be accessed from defined entry points
- [ ] Required components are present
- [ ] Primary actions work as specified
- [ ] Loading state is implemented
- [ ] Empty state is implemented
- [ ] Error state is implemented
- [ ] Permission behavior is implemented
- [ ] Responsive behavior is implemented
- [ ] Accessibility requirements are met

## Feature

- [ ] Primary user flow works end-to-end
- [ ] Alternative flows work
- [ ] Failure flows are handled
- [ ] Analytics events are implemented
- [ ] All open questions are resolved
- [ ] Design has been reviewed
- [ ] Product has approved the specification

---

# 21. Design Handoff Notes

### Figma / Prototype

[Link or reference]

### Design System

[Design system / component library]

### Existing Components to Reuse

- [Component]
- [Component]

### New Components Required

- [Component]
- [Component]

### Design Tokens

- **Typography:** [Reference]
- **Spacing:** [Reference]
- **Colors:** [Reference]
- **Radius:** [Reference]
- **Elevation:** [Reference]

---

# 22. Revision History

| Version | Date | Author | Changes |
|---|---|---|---|
| 0.1 | [Date] | [Name] | Initial draft |
| 0.2 | [Date] | [Name] | [Changes] |
| 1.0 | [Date] | [Name] | Approved |
