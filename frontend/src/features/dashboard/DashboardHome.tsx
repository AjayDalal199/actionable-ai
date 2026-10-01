import { Link } from "@tanstack/react-router"
import { Check } from "lucide-react"
import type { ReactNode } from "react"

import { useAuth } from "@/features/auth/useAuth"
import { CreateWorkspaceForm } from "@/features/workspace/CreateWorkspaceForm"
import { useCurrentWorkspace } from "@/features/workspace/queries"
import { WorkspaceLoadError } from "@/features/workspace/WorkspaceGate"
import { cn } from "@/shared/lib/utils"
import { Button } from "@/shared/ui/button"
import { Skeleton } from "@/shared/ui/skeleton"

export function DashboardHome() {
  const { user: currentUser } = useAuth()
  const {
    data: workspace,
    isError,
    isFetching,
    isPending,
    refetch,
  } = useCurrentWorkspace()

  return (
    <div className="flex flex-col gap-8">
      <div>
        <p className="text-muted-foreground max-w-sm truncate">
          Hi, {currentUser?.full_name || currentUser?.email}
        </p>
        <h1 className="mt-1 text-2xl font-bold tracking-tight">Quick Start</h1>
        <p className="text-muted-foreground mt-1">
          Name your workspace → upload a doc → ask a question
        </p>
      </div>

      {isPending ? (
        <QuickStartSkeleton />
      ) : isError ? (
        <WorkspaceLoadError
          loading={isFetching}
          onRetry={() => {
            void refetch()
          }}
        />
      ) : (
        <ol className="grid gap-4">
          <QuickStartStep
            done={Boolean(workspace)}
            n={1}
            title="Name your workspace"
            description={
              workspace
                ? workspace.name
                : "Create a workspace to isolate knowledge, tools, and chat."
            }
          >
            {workspace ? null : <CreateWorkspaceForm />}
          </QuickStartStep>
          <QuickStartStep
            disabled={!workspace}
            n={2}
            title="Upload a document"
            description="Add a PDF or Markdown file so the agent has something to answer from."
          >
            {workspace ? (
              <Button asChild>
                <Link to="/dashboard/knowledge">Go to Knowledge</Link>
              </Button>
            ) : (
              <Button disabled>Go to Knowledge</Button>
            )}
          </QuickStartStep>
          <QuickStartStep
            disabled={!workspace}
            n={3}
            title="Ask a question"
            description="Try the internal chat once a document is in the knowledge base."
          >
            {workspace ? (
              <Button asChild variant="outline">
                <Link to="/dashboard/chat">Go to Chat</Link>
              </Button>
            ) : (
              <Button disabled variant="outline">
                Go to Chat
              </Button>
            )}
          </QuickStartStep>
        </ol>
      )}
    </div>
  )
}

function QuickStartSkeleton() {
  return (
    <div className="grid gap-4">
      {Array.from({ length: 3 }).map((_, index) => (
        <Skeleton className="h-28 w-full rounded-xl" key={index} />
      ))}
    </div>
  )
}

function QuickStartStep({
  children,
  description,
  disabled = false,
  done = false,
  n,
  title,
}: {
  children?: ReactNode
  description: string
  disabled?: boolean
  done?: boolean
  n: number
  title: string
}) {
  return (
    <li className={cn("rounded-xl border p-5", disabled && "opacity-60")}>
      <div className="flex items-start gap-4">
        <span
          className={cn(
            "flex size-8 shrink-0 items-center justify-center rounded-full text-sm font-semibold",
            done
              ? "bg-primary text-primary-foreground"
              : "bg-muted text-muted-foreground",
          )}
        >
          {done ? <Check className="size-4" /> : n}
        </span>
        <div className="flex min-w-0 flex-1 flex-col gap-3">
          <div>
            <p className="font-medium">{title}</p>
            <p className="text-muted-foreground mt-1 text-sm">{description}</p>
          </div>
          {children}
        </div>
      </div>
    </li>
  )
}
