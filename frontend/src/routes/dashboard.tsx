import { createFileRoute, redirect } from "@tanstack/react-router"

import { isLoggedIn } from "@/features/auth/session"
import { DashboardLayout } from "@/features/dashboard/DashboardLayout"

export const Route = createFileRoute("/dashboard")({
  component: DashboardLayout,
  beforeLoad: async () => {
    if (!isLoggedIn()) {
      throw redirect({
        to: "/login",
      })
    }
  },
})
