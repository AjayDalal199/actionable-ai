import { createFileRoute } from "@tanstack/react-router"

import { DashboardHome } from "@/features/dashboard/DashboardHome"

export const Route = createFileRoute("/dashboard/")({
  component: DashboardHome,
  head: () => ({
    meta: [
      {
        title: "Dashboard — Actionable AI",
      },
    ],
  }),
})
