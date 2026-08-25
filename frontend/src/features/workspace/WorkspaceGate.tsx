import { Link } from "@tanstack/react-router"
import { FolderKanban } from "lucide-react"
import type { ReactNode } from "react"

import { useCurrentWorkspace } from "@/features/workspace/queries"
import { Button } from "@/shared/ui/button"
import { LoadingButton } from "@/shared/ui/loading-button"
import { Skeleton } from "@/shared/ui/skeleton"

export function WorkspaceGate({
  children,
  feature,
}: {
  children: ReactNode
  feature: string
}) {
  const {
    data: workspace,
    isError,
    isFetching,
    isPending,
    refetch,
  } = useCurrentWorkspace()

  if (isPending) {
    return <Skeleton className="h-48 w-full rounded-xl" />
  }

  if (isError) {
    return (
      <WorkspaceLoadError
        loading={isFetching}
        onRetry={() => {
          void refetch()
        }}
      />
    )
  }

  if (!workspace) {
    return <NeedsWorkspace feature={feature} />
  }

  return children
}

export function WorkspaceLoadError({
  loading = false,
  onRetry,
}: {
  loading?: boolean
  onRetry: () => void
}) {
  return (
    <div className="rounded-xl border p-5">
      <p className="font-medium">Couldn't load your workspace</p>
      <p className="text-muted-foreground mt-1 text-sm">
        Something went wrong. Please try again.
      </p>
      <LoadingButton className="mt-3" loading={loading} onClick={onRetry}>
        Retry
      </LoadingButton>
    </div>
  )
}

function NeedsWorkspace({ feature }: { feature: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="bg-muted mb-4 rounded-full p-4">
        <FolderKanban className="text-muted-foreground h-8 w-8" />
      </div>
      <h2 className="text-lg font-semibold">Create a workspace first</h2>
      <p className="text-muted-foreground mt-1 max-w-md">
        Name a workspace on Quick Start before you can use {feature}.
      </p>
      <Button asChild className="mt-4">
        <Link to="/dashboard">Go to Quick Start</Link>
      </Button>
    </div>
  )
}
