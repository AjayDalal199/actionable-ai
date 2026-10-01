import { createFileRoute } from "@tanstack/react-router"

import { ToolsPage } from "@/features/tools/ToolsPage"

export const Route = createFileRoute("/dashboard/tools")({
  component: ToolsPage,
  head: () => ({
    meta: [
      {
        title: "Tools — Actionable AI",
      },
    ],
  }),
})
