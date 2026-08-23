# Prioritization Matrix (RICE)

*The RICE framework helps prioritize ideas based on Reach, Impact, Confidence, and Effort.*

**Formula:** (Reach * Impact * Confidence) / Effort = RICE Score

*   **Reach:** Estimated % of customer base that will use this (100% = 10, 50% = 5, etc.)
*   **Impact:** (3 = massive, 2 = high, 1 = medium, 0.5 = low, 0.25 = minimal)
*   **Confidence:** (100% = 1, 80% = 0.8, 50% = 0.5)
*   **Effort:** Estimated development time in person-months.

## Ideas Backlog

| Idea Name | Reach | Impact | Confidence | Effort | RICE Score | Decision |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **PR-Triggered Auto-Drafting** (Automated Docs) | 10 (All Admins) | 3 (Massive) | 0.8 (Medium/High) | 2 months | **12.0** | **Do (Core MVP/V1)** |
| **Simple JS Tool Registration API** (Agentic Tools) | 10 (All Devs) | 3 (Massive) | 0.9 (High) | 1 month | **27.0** | **Do (Core MVP)** |
| **"Show Me How" Mode** (UI Guidance) | 5 (End Users) | 2 (High) | 0.5 (Low) | 3 months | **1.6** | **Defer (V2)** |
| **Visual Knowledge Graph** (Internal View) | 2 (Internal only) | 0.5 (Low) | 0.8 (Medium) | 2 months | **0.4** | **Drop** |

## Summary
The scoring validates that we must focus our initial MVP and V1 efforts on the **Simple JS Tool Registration API** (highest RICE score due to low effort/high impact) and the **PR-Triggered Auto-Drafting**. 
Complex UI features like "Show Me How" mode should be deferred to later versions, and the Knowledge Graph is dropped entirely for now.
