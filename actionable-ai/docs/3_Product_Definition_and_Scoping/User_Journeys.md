# User Journeys: Actionable AI (A²I) Platform

This document outlines the core paths users take through the A²I Platform to achieve their goals.

---

## Journey 1: The "Quick Start" Onboarding (The Developer)
**Goal:** Prove the platform works (TTV < 5 minutes) before committing to a full GitHub integration.

1.  **Sign Up:** David (Lead Engineer) signs up on the A²I website.
2.  **Workspace Creation:** He is prompted to name his Workspace (e.g., "Acme Corp").
3.  **Manual Ingestion:** David uploads a PDF of Acme's recent API documentation and a Markdown file of FAQs.
4.  **Instant Sandbox:** The system chunks and embeds the files. Within 60 seconds, David is redirected to a "Sandbox Chat" where he can ask questions about the uploaded files.
5.  **Widget Export:** Satisfied, David copies the `<script>` tag provided by the dashboard and pastes it into his local development environment to see the floating widget live.

---

## Journey 2: Agentic Tool Execution (The End-User)
**Goal:** Complete a task using the chatbot without navigating the UI manually.

1.  **Query Intent:** Alex (End-User) opens the A²I widget on Acme Corp's billing page and types, "I want to cancel my subscription."
2.  **Retrieval & Routing:** The A²I orchestrator analyzes the intent. It realizes this matches a registered "Write" tool (`cancel_subscription_api`).
3.  **HITL Confirmation:** Because it is a destructive "Write" action, the widget uses Optimistic UI to instantly render a confirmation card: *"I can cancel your subscription. Are you sure you want to proceed? [Yes, Cancel] [No, keep it]"*.
4.  **Execution:** Alex clicks "Yes". The widget passes Alex's secure JWT token to the backend, calls Acme Corp's API, and returns a success message: *"Your subscription has been successfully canceled."*

---

## Journey 3: [V1] Continuous Documentation (The PM)
**Goal:** Keep customer-facing documentation updated automatically when engineers ship code.

1.  **Code Merge:** David merges a Pull Request adding a "Dark Mode" feature to the `main` branch.
2.  **Webhook Trigger:** GitHub sends a webhook to the A²I Platform. A background worker begins a `diff`-based vector DB sync.
3.  **Auto-Drafting:** The LLM reads the PR description and Jira ticket, generating a draft support article: "How to Enable Dark Mode".
4.  **Review Notification:** Sarah (PM) receives an email alert: "New documentation requires approval."
5.  **Approval:** Sarah logs into the A²I Dashboard, reviews the generated Markdown, tweaks a single sentence for clarity, and clicks "Publish". The chatbot is instantly updated to answer questions about Dark Mode.

---

## Journey 4: Human Handoff (Support Escalation)
**Goal:** Seamlessly transition a frustrated user to a human agent.

1.  **Out-of-Scope Query:** An end-user asks a highly specific, undocumented question: "Why did my API rate limit trigger at 490 requests instead of 500?"
2.  **Graceful Failure:** The A²I orchestrator searches the Vector DB but finds low-confidence chunks. It triggers the fallback protocol.
3.  **Data Collection:** The widget replies: *"I don't have the exact answer for that, but I can connect you with our engineering support team. What's the best email to reach you?"*
4.  **Escalation:** The user provides their email. The A²I backend bundles the entire chat transcript, user context, and email, firing a webhook directly into Acme Corp's Zendesk instance to create a high-priority ticket.
