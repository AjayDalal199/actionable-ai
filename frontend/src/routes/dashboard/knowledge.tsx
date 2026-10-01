import { createFileRoute } from "@tanstack/react-router"

import { KnowledgePage } from "@/features/knowledge/KnowledgePage"

export const Route = createFileRoute("/dashboard/knowledge")({
  component: KnowledgePage,
  head: () => ({
    meta: [
      {
        title: "Knowledge — Actionable AI",
      },
    ],
  }),
})
