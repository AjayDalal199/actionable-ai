# Ideation Workshop Notes

## Workshop Details
*   **Date:** [Assumed Date]
*   **Goal:** Brainstorm specific features that solve the core problems of disconnected documentation and lack of agentic frontend execution, based on our assumed market and user needs.
*   **Participants:** Product Manager, Lead Engineer (Assumed Roles)

## Proposed Ideas

*   **Idea 1: PR-Triggered Auto-Drafting:** Instead of a generic "sync", the system listens specifically to Pull Requests merged into `main`. It analyzes the diff, generates a draft support article, and pings the PM on Slack to review and approve it.
*   **Idea 2: "Show Me How" Mode:** A feature where the chatbot doesn't just execute the action silently, but visually highlights the UI elements (using CSS overlays) and guides the user through the process step-by-step, teaching them how to do it next time.
*   **Idea 3: Simple JS Tool Registration API:** A dead-simple JavaScript API for developers to register functions in the frontend (e.g., `window.Agent.register({ name: "export", func: exportData })`). The backend automatically parses the schema and provides it to the LLM.
*   **Idea 4: Visual Knowledge Graph:** An internal dashboard view that shows a node-graph of all generated documentation and how it links back to specific files in the code repository.

## Action Items
*   [x] Take these ideas into the Prioritization Matrix for scoring.
