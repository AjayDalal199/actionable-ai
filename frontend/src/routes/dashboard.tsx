import { createFileRoute, redirect } from "@tanstack/react-router"

import { clearAccessToken, isLoggedIn } from "@/features/auth/session"
import { DashboardLayout } from "@/features/dashboard/DashboardLayout"
import {
  currentWorkspaceQueryOptions,
  workspacesQueryOptions,
} from "@/features/workspace/queries"
import { isInvalidSessionError } from "@/shared/lib/errors"

export const Route = createFileRoute("/dashboard")({
  component: DashboardLayout,
  beforeLoad: async () => {
    if (!isLoggedIn()) {
      throw redirect({
        to: "/login",
      })
    }
  },
  loader: async ({ context }) => {
    try {
      await Promise.all([
        context.queryClient.ensureQueryData(currentWorkspaceQueryOptions),
        context.queryClient.ensureQueryData(workspacesQueryOptions),
      ])
    } catch (error) {
      if (isInvalidSessionError(error)) {
        clearAccessToken()
        throw redirect({ to: "/login" })
      }
      throw error
    }
  },
  staleTime: Number.POSITIVE_INFINITY,
})
