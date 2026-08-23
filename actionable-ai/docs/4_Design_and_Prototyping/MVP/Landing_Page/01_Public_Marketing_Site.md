# UI/UX Specification: Public Landing Page

## Document Metadata

- **Product:** Actionable AI (A²I) Platform
- **Feature:** Public marketing site (`/`)
- **Version:** MVP (Phase 1)
- **Status:** Draft
- **Owner:** Product Team
- **Last Updated:** 2026-08-23
- **Replaces:** Previous public marketing site spec (teal / slate-blue visual system retired)

---

## 1. Feature Overview

### Purpose

Convert B2B visitors — especially developers evaluating an embeddable agent — into signed-up users. The page must make three things obvious in under ten seconds:

1. This is not a chatbot that dumps help-center links.
2. The agent can execute the visitor’s own APIs and UI actions.
3. Destructive work never runs without a human confirmation.

### User Goal

Understand the product, trust that write-actions are gated, and start a free account without talking to sales.

### Primary Users

| Persona | Role on this page |
| --- | --- |
| David, Lead Engineer (Integrator) | Primary buyer. Scans for time-to-value, API mapping, bundle size, HITL. |
| Sarah, Product / Technical Writer | Secondary. Looks for knowledge quality and review control. |
| Evaluator (security / founder) | Skims HITL, isolation, and data handling before approving a trial. |

End-users of *client* apps do not land here. Do not write copy as if they do.

### Entry Points

- Direct visit to `https://<product-domain>/`
- Referral from docs, GitHub, or engineering posts
- Logged-out visits to other public routes that link home

### Success Criteria

- Visitor can explain, in one sentence, that A²I embeds an agent which answers from uploaded knowledge *and* calls registered tools with HITL on writes.
- Primary CTA (`Get started for free`) is visible above the fold and again at the close.
- Logged-in users who hit `/` go to the dashboard; logged-out users see this page (the current `/` → `/login` redirect is wrong and must be removed).
- No 404s from header/footer links. If a destination is not shipped, omit the link.

---

## 2. Positioning

**One-liner:** Embed an agent that answers from your docs and does the work in your product.

**Category:** Developer infrastructure for in-product agents. Not a helpdesk, not a generic chatbot builder, not a LangChain tutorial.

**Promise:** Live on a client site in minutes: upload knowledge, register actions, drop one script tag.

**Proof the page must show, not claim:** a chat that turns “cancel my subscription” into a confirmation of **that action** in plain language — then Go back / Confirm. Never show an endpoint in the widget.

**Do not say on this page:** MVP, v1, LangChain, architecture codenames, “coming soon” as a feature, “enterprise-grade” without a concrete control next to it.

---

## 3. Brand & visual direction

The previous marketing visual system used teal as the brand accent. Teal is retired. Neutrals stay zinc (true gray, not slate-blue). The product still reads as a **control surface**: high contrast, full-bleed, left-aligned, no decorative chrome.

### 3.1 Accent: ember

**Ember** (`orange`) is the only brand color. It is the *act* signal — primary buttons, text links, active nav, the confirm control on HITL cards. It is not decoration.

| Token | Dark (default) | Light | Use |
| --- | --- | --- | --- |
| Background | `#09090B` | `#FAFAF9` | Page canvas |
| Surface | `#18181B` | `#FFFFFF` | Header, cards, panels |
| Elevated | `#27272A` | `#F5F5F4` | Hover, code chrome, agent bubbles |
| Border | `#3F3F46` | `#E7E5E4` | 1px rules |
| Text | `#FAFAFA` | `#18181B` | Headings, body |
| Muted text | `#A1A1AA` | `#57534E` | Supporting copy (≥ 4.5:1) |
| **Accent** | `#F97316` | `#C2410C` | Primary CTA, links, active states |
| Accent hover | `#FB923C` | `#9A3412` | Hover / focus of accent |
| Accent foreground | `#1C1008` | `#FFFFFF` | Text/icons on accent fills |
| Danger | `#F87171` | `#DC2626` | HITL cancel, destructive only |
| Success | `#34D399` | `#059669` | Connected / confirmed |

Why ember, not teal or blue: teal looked medical/SaaS; `#2563EB` looks like every dashboard kit. Ember is the industrial “execute” color on a dark instrument panel. One accent only. No second brand color. No gradients, glow, or glass.

### 3.2 Type and layout

- **Sans:** Inter. **Mono:** JetBrains Mono (endpoints, script tags, IDs only).
- **Display:** `clamp(2.75rem, 6vw, 4.5rem)`, weight 600, tracking `-0.03em`, line-height 1.05.
- **Section title:** `clamp(1.75rem, 3vw, 2.5rem)`, weight 600, tracking `-0.02em`.
- **Subhead:** 18–20px / 400 / 1.5. **Body:** 16px / 400 / 1.6. **Meta:** 13–14px / 500.
- Marketing type is **left-aligned**. Centered heroes are banned.
- **Full width.** No centered `72rem` island. Horizontal gutter only: 16 / 24 / 32 / 40px at `sm / lg / xl`.
- Split sections: copy left, artifact right. Stack to a single column below `lg`, copy first.
- Separate bands with a 1px border, not a new background *and* a gap *and* a shadow.
- Radius 8px on buttons/cards; 4px on badges. No pills except status dots.
- Motion: 150ms ease-out on hover/open. No scroll-fade of above-the-fold content. Honor `prefers-reduced-motion`.
- Default theme: dark. Light mode is first-class (same structure, ember darkened for contrast on paper).

### 3.3 Buttons

- Primary: solid ember, accent-foreground text, height 40px, radius 8px.
- Secondary: 1px border, transparent fill, hover = elevated surface.
- Danger: solid danger, white (light) / near-white (dark) text. HITL Cancel only.
- No drop shadows. No gradient fills.

---

## 4. User flow

### Primary flow

```text
Land on /
    ↓
Scan hero (headline + HITL artifact)
    ↓
Optional: How it works / Security
    ↓
Click "Get started for free"
    ↓
/signup
    ↓
Authenticated → /dashboard
```

### Alternative flows

```text
Click "Log in" → /login
Click "Documentation" → public docs (or omit until docs exist)
Already logged in + visit / → redirect /dashboard
```

### Failure flows

- Signup/login errors are handled on those routes, not here.
- Broken footer links are a spec failure: do not ship placeholders.

---

## 5. Information architecture

```text
Public site
├── /                  Landing page (this spec)
├── /login
├── /signup
├── /recover-password
├── /docs              Optional; hide nav item until real
├── /terms             Required before public launch
└── /privacy           Required before public launch
```

In-page anchors on `/`: `#how-it-works`, `#security`, `#faq`.

---

## 6. Screen: Landing page

### Route

`/`

### Layout (desktop)

```text
┌──────────────────────────────────────────────────────────────┐
│ Logo    How it works  Security  Docs     Log in  Get started │
├──────────────────────────────────────────────────────────────┤
│ Headline + subhead + CTAs     │  Chat + HITL artifact        │
├──────────────────────────────────────────────────────────────┤
│ Proof strip: time-to-value · HITL on writes · one script tag │
├──────────────────────────────────────────────────────────────┤
│ Problem: three columns                                       │
├──────────────────────────────────────────────────────────────┤
│ How it works: 01  02  03                                     │
├──────────────────────────────────────────────────────────────┤
│ Capabilities: four rows, copy | artifact alternating         │
├──────────────────────────────────────────────────────────────┤
│ Security / HITL spotlight                                    │
├──────────────────────────────────────────────────────────────┤
│ Who it is for: Integrator · Writer · End-user of *their* app │
├──────────────────────────────────────────────────────────────┤
│ Compare: help-center bot vs A²I agent                        │
├──────────────────────────────────────────────────────────────┤
│ FAQ                                                          │
├──────────────────────────────────────────────────────────────┤
│ Closing CTA band                                             │
├──────────────────────────────────────────────────────────────┤
│ Footer                                                       │
└──────────────────────────────────────────────────────────────┘
```

---

## 7. Global chrome

### 7.1 Header

Sticky, opaque surface, 1px bottom border, 64px tall, full-width gutter.

- **Left:** Wordmark “Actionable AI” (not “A²I” in chrome — too cute for a first visit).
- **Nav (lg+):** How it works → `#how-it-works`; Security → `#security`; Documentation → `/docs` only if that route exists.
- **Right:** Log in (secondary / ghost) → `/login`; Get started (primary) → `/signup`.
- **Below lg:** logo + icon button. Mobile nav is a **top-layer dialog**, not a drawer trapped under the sticky header. Same links plus both CTAs stacked.

Do not put pricing, blog, or changelog in the header until those pages exist.

### 7.2 Footer

1px top border. Four columns on desktop, stacked on mobile.

| Product | Developers | Legal | Company |
| --- | --- | --- | --- |
| How it works (`#how-it-works`) | Documentation (if live) | Terms of Service | Contact (mailto or form) |
| Security (`#security`) | — | Privacy Policy | — |

Copyright: `© {year} Actionable AI`. No social icons unless profiles exist. No “Pricing” until a pricing page ships.

---

## 8. Sections and copy

Lock this copy unless a rewrite is explicitly requested. Voice: direct, concrete, second person. Short sentences. Name the mechanism (OpenAPI, HITL, Shadow DOM) once, then say what it does for the reader.

### 8.1 Hero

**Eyebrow (optional, 13px meta):** Agent infrastructure for SaaS products

**Headline:** Give your product an agent that can actually do things.

**Subheadline:** Embed a widget that answers from your docs, does the work in your product, and asks before anything that cannot be undone. Live in minutes, not a quarter.

**Primary CTA:** Get started for free → `/signup`

**Secondary CTA:** See how it works → `#how-it-works`

**Artifact (right column):** Static but high-fidelity mock of the embeddable widget.

1. User: `Cancel my Pro subscription.`
2. Agent: `I can cancel your Pro plan. This cannot be undone.`
3. HITL card:
   - Title: `Cancel your Pro plan`
   - Badge: `Cannot be undone` (danger color, not ember)
   - Consequence in body copy. **No HTTP method, path, tool name, or “API.”**
   - Buttons: Go back (danger fill) · Confirm (ember fill), equal height, 8px gap

The artifact is the product, not an illustration of people-plus-robots. No stock photos. No lottie blobs.

### 8.2 Proof strip

Three facts, not logos (no customers to name yet). Do not fake company marks.

| Fact | Label |
| --- | --- |
| Under 5 minutes | Upload docs, register a tool, copy one script tag |
| Confirm before it happens | They confirm the action. Then the agent does it. |
| Isolated widget | Shadow DOM. Your CSS does not leak in; ours does not leak out |

If a real customer exists later, replace this strip with a logo row *and keep* the three facts as a second line — logos without a claim are empty.

### 8.3 Problem

**Section title:** Most in-product chat still leaves the user to finish the job.

**Intro (one sentence):** Documentation lags the codebase, bots paste article links, and a safe agent that can call production APIs usually means a custom project.

Three columns:

1. **Stale knowledge**  
   The bot answers from a wiki that last matched the product two releases ago.

2. **Passive answers**  
   “Go to Settings → Billing → Cancel” is not help. It is a reading assignment.

3. **Unsafe or unshippable agents**  
   Wiring tool-calling without a confirmation gate is how refunds and deletes escape into production.

No “pain points” heading. The title already states the problem.

### 8.4 How it works (`#how-it-works`)

**Section title:** Three steps. Then it lives in your app.

Numbered 01 / 02 / 03, left-aligned, mono numerals.

1. **Feed it what you already have**  
   Drop PDFs, Markdown, or pasted API docs. The agent retrieves from that corpus immediately. No repo connection required for the first trial.

2. **Register the hands**  
   Point at OpenAPI, a JSON schema, or a client-side function. Mark each tool read or write. Writes lock HITL on.

3. **Drop the widget**  
   One script tag, Shadow DOM, signed user context. The same agent your visitor just tested is now on their product.

Each step may show a small artifact: file list → schema snippet → `<script src="…">`. Keep snippets short enough to read without scrolling sideways on mobile.

### 8.5 Capabilities

**Section title:** Built to act, with a brake.

Four split rows. Alternate artifact side on desktop (copy | visual, then visual | copy). Same order in the DOM for screen readers: heading, body, artifact.

1. **Bring your own APIs**  
   Paste OpenAPI or a JSON schema. The platform maps endpoints to LLM tools. You keep the APIs; the agent gets a typed contract.

2. **Knowledge in minutes**  
   Upload policies, manuals, and product docs. Retrieval is the default path for questions that should not hit a tool.

3. **Human-in-the-loop on writes**  
   Writes show a confirmation card: what will happen, in plain language. They confirm or go back. They never see an API. Nothing runs until they confirm.

4. **A widget that will not fight your CSS**  
   Shadow DOM isolation, small payload, XSS sanitization. Built so an engineer can ship it without a design-system collision.

Do not add a fifth card for “AI-powered” or “enterprise security.” Security has its own section.

### 8.6 Security spotlight (`#security`)

**Section title:** The agent does not get a blank check.

**Body:** Every session carries a signed user token. Tools are classified read or write. Write execution waits on an explicit confirm in the widget. Cancel aborts; the model does not retry the same call quietly. Your backend remains the source of authorization — the platform does not invent permissions.

**Artifact:** Annotated HITL card callouts:

- The action → what will happen, in their words
- The consequence → enough to decide, no endpoint
- Go back = abort, Confirm = do it
- Footnote: “No confirm → nothing runs”

The person using the client’s product confirms the **action**. Endpoints exist only in the integrator dashboard.

This section is the trust closer for David and for whoever signs off on the trial. Keep language operational. Do not cite SOC2 or GDPR as if they were shipped (they are not, in MVP).

### 8.7 Who it is for

**Section title:** One platform, three jobs.

| Audience | They use A²I to |
| --- | --- |
| Engineering | Ship a support/agent surface without a custom orchestration project. Register `refundUser`, `upgradePlan`, `exportReport` against real endpoints. |
| Product / docs | Put current manuals in front of the agent and keep customer-facing wording accurate. |
| Their end-users | Ask in the product and get the task offered, not a tour of the settings tree. |

Write “their end-users,” never “you, the customer of our customer” in the headline.

### 8.8 Compare

**Section title:** A help-center bot vs an actionable agent

Two-column table. Left is the default they already know. Right is A²I. Do not name competitors.

| | Help-center chatbot | Actionable AI |
| --- | --- | --- |
| Question: “How do I export?” | Link to an article | Offer to run export, then do it |
| Knowledge | Static articles | Uploaded corpus (repo sync later) |
| Write actions | None, or hidden automations | Visible HITL card |
| Install | Another Intercom-shaped bubble | One isolated script |

Keep the table to four rows. This is orientation, not a feature matrix.

### 8.9 FAQ (`#faq`)

Accordion. One question open at a time. Answers in body size, not legal fine print.

**Do I need to connect GitHub to try this?**  
No. Upload documents and register tools by hand. Repository sync is a later path, not the front door.

**What happens if the agent wants to delete or charge?**  
That is a write. The widget asks them to confirm the action in plain language. Confirm does it. Go back does not. They never see an API.

**Will this restyle our app?**  
The widget runs in Shadow DOM. Host CSS stays out; widget CSS stays in.

**Is there a free tier?**  
Yes. Create an account, ingest a small corpus, and embed the widget. Paid limits and automation come after you have a working agent.

**Where does user data go?**  
Chat and tool calls run through the A²I backend so the model can retrieve and act. You authorize actions with a signed user context. Full data-processing terms live in the Privacy Policy. (Link it. Do not improvise a compliance essay here.)

**Can we talk to sales?**  
For volume, SSO, or a security review, use Contact. The default path is self-serve signup.

### 8.10 Closing CTA

**Headline:** Ship the agent this week.

**Subhead:** Create an account, upload a manual, register one action, paste the script tag.

**Primary CTA:** Get started for free → `/signup`

**Secondary:** Log in → `/login`

No testimonial block until there is a real quote with a real name and company.

---

## 9. Components (page-specific)

### HITL artifact (marketing)

- Surface fill, **1px danger border**, 16px padding, 8px radius.
- Title left: the action in plain language. Badge right: `Cannot be undone` when true.
- Body: consequence the user needs to decide. **No** HTTP method, path, tool id, or “API.”
- Go back = danger fill. Confirm = ember fill.
- Decorative only on `/`. Do not bind it to a live API.

### Widget frame

- Elevated chat panel, ~360px wide in the hero, 8px radius, 1px border.
- User bubbles: ember fill, accent-foreground text, right aligned.
- Agent bubbles: elevated fill, left aligned. Not comic-strip tails.
- Input chrome at the bottom may be visual-only (disabled) so visitors do not think they are chatting with production.

### FAQ accordion

- Button is the question (section-adjacent 16–18px, weight 500).
- Chevron rotates 150ms. Collapsed answer is not in the accessibility tree as a visible region (`aria-expanded`).

---

## 10. States, responsive, accessibility

- **Default:** dark theme from system or stored preference; same as the app.
- **Loading:** this page is static. No page-level spinner. Header CTAs are always enabled.
- **Logged-in visit to `/`:** redirect to `/dashboard` (no flash of marketing if avoidable).
- **lg+:** split hero and split capability rows.
- **Below lg:** single column, gutted padding 16px, hero artifact under copy, table in compare scrolls horizontally if needed rather than wrapping into unreadability.
- **Focus:** `0 0 0 2px <background>, 0 0 0 4px <accent>`.
- **Contrast:** body and muted text meet WCAG AA on both themes. Ember buttons: use the token table; do not put orange-400 text on zinc-900 as body copy.
- Skip link: “Skip to content” targeting the hero heading.
- Anchor nav must not be the only way to reach How it works / Security / FAQ.

---

## 11. SEO, social, analytics

**Title:** Actionable AI — An agent that answers and acts  
**Meta description:** Embed an AI agent in your product. It answers from your docs, does the work, and asks a human to confirm the action first.

**Open Graph / Twitter:** dark hero crop (headline + HITL card), 1200×630. Alt text: “Actionable AI landing page showing a chat confirmation to cancel a subscription.”

**H1:** the hero headline, once. Section titles are `h2`. FAQ questions are `h3`.

**Analytics events (minimum):**

| Event | When |
| --- | --- |
| `landing_view` | Page view |
| `cta_get_started` | Any “Get started” click, with `placement`: `header` \| `hero` \| `footer_band` |
| `cta_login` | Log in click |
| `nav_anchor` | In-page nav, with `target` id |

No fake live-chat widget on the marketing page. It competes with the product screenshot.

---

## 12. Out of scope (MVP page)

- Pricing page and plan comparison
- Blog, changelog, careers
- Interactive sandbox on `/` (belongs post-signup)
- Customer logo wall, invented quotes
- SOC2 / GDPR badges
- Localization
- Cookie banner until legal requires it; if required, keep it a bar, not a modal that blocks the hero

---

## 13. Implementation notes

- `/` is a public route. Auth redirect applies only when the session is valid (send those users to `/dashboard`).
- Reuse app tokens for color/type; do not introduce a second marketing CSS universe. Swap teal tokens for ember in the shared theme when this page is built.
- Prefer CSS and static markup for the HITL mock. No scroll-driven fade of the hero.
- Legal pages may use `max-width: 65ch`, still left-aligned to the gutter.
