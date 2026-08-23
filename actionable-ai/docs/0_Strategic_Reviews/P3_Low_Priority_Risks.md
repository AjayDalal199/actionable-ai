# P3: Low Priority Risks (Nuisances & Polish)

*Priority Level: P3 (Low)*
*Urgency: Polish / Bug Fixes post-launch*
*Nature: These risks will not stop adoption or cause data loss, but represent minor security nuisances, visual glitches, or sub-optimal performance edges.*

---

## 1. Markdown XSS Injection via LLM Output
*   **The Risk:** If the LLM goes rogue or is tricked into outputting a markdown response containing raw HTML (e.g., `<script>alert('xss')</script>`), and our frontend widget's markdown parser doesn't sanitize HTML, we essentially execute an XSS attack on our client's website.
*   **The Fix:** The frontend widget must utilize a strict HTML sanitizer library (like `DOMPurify`) immediately after parsing the markdown to stringently strip all `<script>` tags, `onload` events, and potentially dangerous SVGs before rendering to the DOM.

## 2. Streaming JSON Parse Jitter
*   **The Risk:** When the LLM is deciding to call a tool, it streams a JSON object back to the server. If the frontend tries to eagerly parse this stream to show "loading states" for specific tools, parsing incomplete JSON throws constant errors, causing console spam or UI flickering.
*   **The Fix:** The backend orchestration layer should buffer the tool-calling JSON internally. It should only emit a standard "Executing Tool..." Server-Sent Event (SSE) to the frontend, rather than forcing the frontend to parse broken JSON streams.
