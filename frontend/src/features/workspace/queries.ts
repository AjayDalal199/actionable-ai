import { type QueryClient, queryOptions, useQuery } from "@tanstack/react-query"

import { WorkspacesService } from "@/api"
import { authKeys } from "@/features/auth/queries"
import { isLoggedIn } from "@/features/auth/session"
import { itemKeys } from "@/features/items/queries"
import { getHttpErrorDetail, getHttpErrorStatus } from "@/shared/lib/errors"

export const workspaceKeys = {
  current: ["workspace", "me"] as const,
  list: ["workspaces"] as const,
  members: ["workspace", "members"] as const,
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

export const workspacesQueryOptions = queryOptions({
  queryKey: workspaceKeys.list,
  queryFn: async () => (await WorkspacesService.readWorkspaces()).data,
  staleTime: Number.POSITIVE_INFINITY,
})

export function useCurrentWorkspace() {
  return useQuery({
    ...currentWorkspaceQueryOptions,
    enabled: isLoggedIn(),
  })
}

export function useWorkspaces() {
  return useQuery({
    ...workspacesQueryOptions,
    enabled: isLoggedIn(),
  })
}

export function membersQueryOptions(workspaceId: string) {
  return queryOptions({
    queryKey: [...workspaceKeys.members, workspaceId] as const,
    queryFn: async () => (await WorkspacesService.readWorkspaceMembers()).data,
    staleTime: Number.POSITIVE_INFINITY,
  })
}

export function useWorkspaceMembers(workspaceId: string | undefined) {
  return useQuery({
    ...membersQueryOptions(workspaceId ?? ""),
    enabled: isLoggedIn() && Boolean(workspaceId),
  })
}

export function invalidateWorkspaceSession(queryClient: QueryClient) {
  return Promise.all([
    queryClient.invalidateQueries({ queryKey: workspaceKeys.current }),
    queryClient.invalidateQueries({ queryKey: workspaceKeys.list }),
    queryClient.invalidateQueries({ queryKey: workspaceKeys.members }),
    queryClient.invalidateQueries({ queryKey: authKeys.currentUser }),
    queryClient.invalidateQueries({ queryKey: itemKeys.all }),
  ])
}
