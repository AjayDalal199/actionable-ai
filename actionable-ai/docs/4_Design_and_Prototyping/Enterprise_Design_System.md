# Enterprise UI Design System: Actionable AI (A²I)

*This document defines the strict visual language for the A²I Platform. As a B2B enterprise application, our UI must project trust, reliability, and precision. We strictly avoid consumer-app trends like heavy gradients, neon glows, and excessive glassmorphism.*

---

## 1. Core Principles
1. **Clarity over Flash:** Data and text must always be immediately legible. 
2. **High Information Density:** B2B users need to see complex data (JSON schemas, API logs) without excessive padding.
3. **Muted Elegance:** Use solid, flat colors and subtle borders. 
4. **Accessible Contrast:** All text and interactive elements must pass WCAG AA standards (4.5:1 ratio).
5. **Workflow Simplification:** Minimize steps to complete tasks (like registering tools) and automate repetitive actions to reduce cognitive load.
6. **Data Visualization:** Complex API metrics and RAG analytics must be presented using clear charts and graphs for instant decision-making.

---

## 2. Color Palette (Strictly Solid Colors, No Gradients)

### 2.1. Backgrounds & Surfaces (Theming)
The system supports both Light and Dark modes to accommodate user preference, but defaults to a dark Slate theme to reduce eye strain for developers looking at API logs all day.
*   **App Background:** `#0F172A` (Slate 900) - Used for the main body.
*   **Surface/Card Background:** `#1E293B` (Slate 800) - Used for panels, modals, and the chat widget background.
*   **Elevated Surface:** `#334155` (Slate 700) - Used for dropdown menus and hovering on table rows.
*   **Borders & Dividers:** `#475569` (Slate 600) - Subtle 1px solid lines to separate components.

### 2.2. Primary Actions & Accents
Instead of vibrant neon gradients, we use a trusted, professional "Enterprise Blue".
*   **Primary Button / Accent:** `#2563EB` (Blue 600)
*   **Primary Hover:** `#1D4ED8` (Blue 700)
*   **Focus Ring:** `0 0 0 2px #1E293B, 0 0 0 4px #3B82F6` (Clear, accessible focus state for keyboard navigation).

### 2.3. Semantic System Colors (Status & Alerts)
Used exclusively for status badges (Active/Processing) and the HITL Warning cards.
*   **Success (Active/Confirmed):** `#16A34A` (Green 600) - Text: `#DCFCE7`
*   **Warning (Processing/HITL Action):** `#D97706` (Amber 600) - Text: `#FEF3C7`
*   **Danger (Failed/Delete/Cancel):** `#DC2626` (Red 600) - Text: `#FEE2E2`
*   **Info (Neutral):** `#475569` (Slate 600)

---

## 3. Typography

*   **Primary Font Family:** `Inter`, `Roboto`, or system-ui. (Clean, highly legible sans-serif).
*   **Monospace Font:** `JetBrains Mono` or `Fira Code`. (Used strictly for JSON schema editors and API endpoints).

### 3.1. Type Scale
*   **H1 (Page Title):** 24px / Semi-Bold
*   **H2 (Section Header):** 18px / Medium
*   **H3 (Card Title):** 16px / Medium
*   **Body (Base text):** 14px / Regular (Used for the vast majority of the UI).
*   **Small (Metadata/Badges):** 12px / Medium

---

## 4. Spacing & Grid System

We utilize a strict **8-point grid system** for consistent spacing.
*   **Micro (4px):** Spacing inside small components (e.g., between an icon and text inside a button).
*   **Small (8px):** Standard padding for inputs and buttons.
*   **Medium (16px):** Spacing between components in a form or card padding.
*   **Large (24px):** Spacing between major page sections.
*   **X-Large (32px+):** Outer page margins.

---

## 5. Component Styles

### 5.1. Buttons
*   **Style:** Flat background color, no gradients, sharp or slightly rounded corners (`border-radius: 4px`).
*   **Shadows:** None. Enterprise software relies on clear borders and background contrast, not drop shadows.

### 5.2. Forms & Inputs
*   **Background:** `#0F172A` (Darker than the surface to indicate it's an inset "well").
*   **Border:** `1px solid #475569`. 
*   **Focus State:** Changes border to Primary Blue (`#2563EB`) without glowing.

### 5.3. HITL (Human-in-the-Loop) Confirmation Card
*   **Background:** `#1E293B` (Slate 800)
*   **Border:** `1px solid #DC2626` (Danger Red) to draw immediate, serious attention without looking like a consumer notification.
*   **Layout:** Strict left-aligned text, standard padding (16px), flat solid red button for Cancel, flat solid blue button for Confirm.

### 5.4. Chat Widget Bubbles
*   **AI Bubble:** `#1E293B` (Slate 800), left-aligned.
*   **User Bubble:** `#2563EB` (Primary Blue), right-aligned.
*   **Corners:** `border-radius: 6px`. Clean and structured, not perfectly round or bubbly.

---

## 6. Navigation Systems

Following enterprise best practices (inspired by platforms like HubSpot and SAP), navigation must be highly structured:
*   **Breadcrumbs:** Always present at the top of the workspace to prevent users from getting lost in nested configurations.
*   **Left Sidebar:** Logically grouped (Home, Knowledge, Tools, Settings) with clear, easily identifiable icons.
*   **Split-View Functionality:** For complex tasks (like Sandbox Testing), utilize a split-view layout so users can multitask efficiently without losing context.
