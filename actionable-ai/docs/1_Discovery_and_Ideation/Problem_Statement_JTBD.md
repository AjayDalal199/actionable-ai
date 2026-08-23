# Problem Statement & Jobs to be Done (JTBD)

## Background
Modern web applications frequently update their features and codebases. Keeping documentation in sync is a manual, tedious process, leading to outdated knowledge bases. Furthermore, standard AI chatbots only provide text answers, forcing users to still navigate complex UI to perform the actual actions they are asking about.

## The Core Problem
Companies struggle to maintain accurate, up-to-date AI chatbots because they are disconnected from the actual codebase. Additionally, users experience friction because these chatbots cannot perform client-side actions (tool calling) on their behalf, limiting the bot to just being an answering machine rather than an active assistant.

## Jobs to be Done (JTBD)
*Framework: When [situation], I want to [motivation], so I can [expected outcome].*

*   **JTBD 1 (Developer):** When I push new code and features to the repository, I want the system to automatically analyze the changes and update the chatbot's knowledge, so I don't have to spend hours manually writing and updating documentation.
*   **JTBD 2 (End-User):** When I am confused about how to use a feature on a web app, I want the chatbot to not only tell me how to do it but also offer to navigate me there or perform the action for me, so I can complete my task quickly without frustration.
*   **JTBD 3 (Sales/Support Staff):** When I receive a highly technical question from a prospect, I want to query an internal chatbot that understands the actual codebase, so I can provide an accurate answer without having to interrupt the engineering team.
*   **JTBD 4 (Product Manager):** When the system auto-generates documentation, I want to be able to review and approve it in a draft state, so I can ensure the customer-facing language is appropriate before it goes live.

## User Pain Points
*   **Pain Point 1:** Documentation is always lagging behind the actual product, leading to chatbots giving incorrect or outdated answers.
*   **Pain Point 2:** Chatbots that only return text are frustrating for users who just want a task completed (e.g., "How do I export this?" -> Bot: "Go to settings, click export..." vs Bot: "I can export that for you. [Export Button]").
*   **Pain Point 3:** High technical barrier to entry for setting up reliable agentic workflows that can safely execute client-side JavaScript functions.
