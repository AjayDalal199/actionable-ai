# P2: Medium Priority Risks (Optimizations & Scale)

*Priority Level: P2 (Medium)*
*Urgency: Can be deferred to V1 or V2*
*Nature: These are structural and architectural optimizations. The MVP can survive without them, but they represent significant friction points as the platform scales.*

---

## 1. Unrealistic "Time-to-Value" KPI Expectation
*   **The Risk:** The OKRs stated a goal of users testing the bot in under 5 minutes. However, simultaneously requiring the system to clone, chunk, and embed a massive GitHub repository takes hours, breaking the TTV expectation.
*   **The Fix:** Introduced a "Quick Start" file upload flow (e.g., PDF upload) for instant testing to hit the < 5 minute TTV. Full Code repository syncing was explicitly demoted to a background asynchronous task.

## 2. Multi-Turn Tool Memory Loss
*   **The Risk:** The AI executes a tool (e.g., "Get User Profile"), and two messages later, the user says "Okay, update their email to X". If the system relies on plain text chat history, the LLM will lose track of the structured JSON data returned by the first tool call.
*   **The Fix:** Specified robust **State Management** (e.g., LangGraph) in the API Request Engine. Tool execution results must be stored in a structured "Memory State" object associated with the session, rather than just plain text.

## 3. LLM Vendor Lock-in (Single Point of Failure)
*   **The Risk:** Building the entire orchestration directly around OpenAI's specific tool-calling JSON schema. If OpenAI suffers an extended outage or changes their API, the entire platform goes down.
*   **The Fix:** Added a requirement for an **LLM Abstraction Layer** (like LiteLLM) to the Technical Requirements. This allows the backend to instantly hot-swap between models (GPT-4o, Claude 3.5 Sonnet, Llama 3) without rewriting tool-calling logic.

## 4. Widget CSS Conflicts (Frontend Integration)
*   **The Risk:** The embeddable widget might clash with the client website's CSS. A client's global `button` styles could override ours, or our widget might be hidden behind their `z-index: 9999` modals, resulting in a broken UI.
*   **The Fix:** The frontend widget architecture must enforce strict CSS isolation. It should be built using the **Shadow DOM** or strict CSS Modules (with hashed classes) to prevent styles from leaking in or out.

## 5. Multi-Language Embedding Gaps (Market Expansion)
*   **The Risk:** If a client's RAG documentation is in English, but a global end-user asks a question in Spanish, a basic embedding model will fail to find the semantic overlap, causing the chatbot to fail answering non-English queries.
*   **The Fix:** The system must utilize a **Multi-lingual Embedding Model** (e.g., Cohere Multilingual or `text-embedding-3-small`) to ensure cross-lingual semantic search works naturally out of the box without requiring the client to manually translate their docs.

## 6. Session Flooding & DB Bloat (Zombie States)
*   **The Risk:** A script opens 10,000 anonymous incognito sessions and sends one "hello" message each. Because we maintain robust State Management (Risk #2), we allocate 10,000 memory objects in Postgres. This bloats our database instantly.
*   **The Fix:** Implement aggressive TTL (Time-To-Live) sweeps on anonymous session state objects, deleting memory for inactive widget sessions after 24 hours.

## 7. LLM "Confidently Incorrect" Degradation
*   **The Risk:** When the RAG pipeline fails to find an exact answer in the DB, LLMs are notoriously bad at gracefully admitting ignorance. They often confidently give a generic, slightly wrong answer hallucinated from their pre-training, eroding trust.
*   **The Fix:** Implement strict prompt engineering constraints (e.g., "If the answer is not contained in the `<context>` block, you MUST reply with 'I cannot find the answer.'"). Potentially use a secondary fast LLM judge to evaluate RAG confidence before replying.
