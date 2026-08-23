# OKRs & KPIs (MVP & V1) - Actionable AI (A²I) Platform

## Objectives and Key Results (OKRs)

**Objective 1: Prove the core value proposition of "Actionable AI" with a successful MVP launch (Manual Ingestion & Tools).**
*   **KR 1:** Successfully onboard 10 beta SaaS clients who deploy the widget to a live or staging environment.
*   **KR 2:** Achieve a 70% "Deflection Rate" (queries resolved by the AI without human escalation) across all beta clients.
*   **KR 3:** Ensure that at least 50% of beta clients register at least 3 custom tools (JS functions or APIs) for the AI to use.

**Objective 2: Validate the automated documentation pipeline and GitHub syncing (V1 Rollout).**
*   **KR 1:** Process 500+ pull request descriptions and linked Jira tickets across client repositories to generate accurate customer-facing documentation without critical parsing failures.
*   **KR 2:** Reduce the time it takes a PM/Editor to approve auto-generated docs to under 3 minutes per document.

---

## Key Performance Indicators (KPIs)

These are the ongoing health metrics we will track on our internal dashboard:

### 1. Acquisition & Activation
*   **Time-to-Value (TTV):** The average time from a user creating an account to asking their first successful question in the testing sandbox via the "Quick Start" file upload flow. (Goal: < 5 minutes)
*   **Widget Implementation Rate:** % of signups that actually paste the widget script into their live website.

### 2. Engagement (End-User Value)
*   **Tool Invocation Rate:** The percentage of user conversations where the AI Assistant successfully executes an action (a registered tool) rather than just returning text. (This measures how "Agentic" the bot actually is in practice).
*   **Escalation Rate:** The percentage of conversations that result in an Email/Webhook handoff. (A lower number is generally better, indicating the AI is handling the load).

### 3. Retention (Client Value)
*   **Sync Frequency:** How often clients are pulling updates from their codebase (indicates they rely on the system for up-to-date info).
*   **Active Registered Tools:** The average number of tools/APIs maintained by an active client.
