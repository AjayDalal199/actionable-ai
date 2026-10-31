import { createFileRoute } from "@tanstack/react-router"

import { WidgetPage } from "@/features/widget/WidgetPage"

export const Route = createFileRoute("/dashboard/widget")({
  component: WidgetPage,
  head: () => ({
    meta: [
      {
        title: "Widget — Actionable AI",
      },
    ],
  }),
})
