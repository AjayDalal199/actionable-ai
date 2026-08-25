import { createFileRoute, redirect } from "@tanstack/react-router"

import { isLoggedIn } from "@/features/auth/session"
import { DashboardLayout } from "@/features/dashboard/DashboardLayout"
import { currentWorkspaceQueryOptions } from "@/features/workspace/queries"

export const Route = createFileRoute("/dashboard")({
  component: DashboardLayout,
  beforeLoad: async () => {
    if (!isLoggedIn()) {
      throw redirect({
        to: "/login",
      })
    }
  },
  loader: ({ context }) =>
    context.queryClient.ensureQueryData(currentWorkspaceQueryOptions),
  staleTime: Number.POSITIVE_INFINITY,
})
