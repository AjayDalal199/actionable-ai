import { useQuery } from "@tanstack/react-query"
import { useNavigate, useRouterState } from "@tanstack/react-router"
import { useEffect, useRef } from "react"

import { documentsQueryOptions } from "@/features/knowledge/queries"
import { useCurrentWorkspace } from "@/features/workspace/queries"

/** Open the sandbox when the workspace's first document becomes active. */
export function useFirstDocumentSandbox() {
  const navigate = useNavigate()
  const pathname = useRouterState({
    select: (state) => state.location.pathname,
  })
  const { data: workspace } = useCurrentWorkspace()
  const workspaceId = workspace?.id
  const documents = useQuery({
    ...documentsQueryOptions(workspaceId ?? "pending"),
    enabled: Boolean(workspaceId),
  })
  const baseline = useRef<number | null>(null)
  const trackedWorkspace = useRef<string | null>(null)

  useEffect(() => {
    if (!workspaceId) {
      baseline.current = null
      trackedWorkspace.current = null
      return
    }
    if (trackedWorkspace.current !== workspaceId) {
      trackedWorkspace.current = workspaceId
      baseline.current = null
    }
    const rows = documents.data?.data
    if (!rows) {
      return
    }
    const active = rows.filter((row) => row.status === "active").length
    const prior = baseline.current
    baseline.current = active
    const onSandbox =
      pathname === "/dashboard/chat" || pathname === "/dashboard/chat/"
    if (prior === 0 && active > 0 && !onSandbox) {
      void navigate({ to: "/dashboard/chat" })
    }
  }, [documents.data, navigate, pathname, workspaceId])
}
