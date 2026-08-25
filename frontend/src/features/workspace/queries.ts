import { queryOptions, useQuery } from "@tanstack/react-query"

import { WorkspacesService } from "@/api"
import { isLoggedIn } from "@/features/auth/session"
import { getHttpErrorDetail, getHttpErrorStatus } from "@/shared/lib/errors"

export const workspaceKeys = {
  current: ["workspace", "me"] as const,
}

export function isMissingWorkspaceError(error: unknown): boolean {
  const status = getHttpErrorStatus(error)
  const detail = getHttpErrorDetail(error)
  if (status === 403 && detail === "User is not a member of a workspace") {
    return true
  }
  if (status === 404 && detail === "Workspace not found") {
    return true
  }
  return false
}

export const currentWorkspaceQueryOptions = queryOptions({
  queryKey: workspaceKeys.current,
  queryFn: async () => {
    try {
      return (await WorkspacesService.readWorkspaceMe()).data
    } catch (error) {
      if (isMissingWorkspaceError(error)) {
        return null
      }
      throw error
    }
  },
  staleTime: Number.POSITIVE_INFINITY,
})

export function useCurrentWorkspace() {
  return useQuery({
    ...currentWorkspaceQueryOptions,
    enabled: isLoggedIn(),
  })
}
