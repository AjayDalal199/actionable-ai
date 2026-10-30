import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { MessageSquare } from "lucide-react"
import { useEffect, useRef } from "react"

import type { ChatTurn } from "@/features/chat/useInternalChat"
import { useInternalChat } from "@/features/chat/useInternalChat"
import { documentsQueryOptions } from "@/features/knowledge/queries"
import { useCurrentWorkspace } from "@/features/workspace/queries"
import { WorkspaceGate } from "@/features/workspace/WorkspaceGate"
import { Badge } from "@/shared/ui/badge"
import { Button } from "@/shared/ui/button"
import { LoadingButton } from "@/shared/ui/loading-button"
import { Skeleton } from "@/shared/ui/skeleton"
import { Textarea } from "@/shared/ui/textarea"

export function ChatPage() {
  return (
    <div className="flex h-[calc(100dvh-10.25rem-2px)] min-h-112 flex-col gap-4 md:h-[calc(100dvh-11.25rem-2px)]">
      <div>
        <div className="flex items-center gap-2">
          <h1 className="text-2xl font-bold tracking-tight">Chat</h1>
          <Badge variant="secondary">Sandbox</Badge>
        </div>
        <p
          className="text-muted-foreground mt-1"
          data-testid="chat-sandbox-label"
        >
          Test surface. Questions and actions run as your dashboard account.
        </p>
      </div>
      <WorkspaceGate feature="Chat">
        <ChatWorkspace />
      </WorkspaceGate>
    </div>
  )
}

function ChatWorkspace() {
  const { data: workspace } = useCurrentWorkspace()
  if (!workspace) {
    return null
  }
  return <ChatReady key={workspace.id} workspaceId={workspace.id} />
}

function ChatReady({ workspaceId }: { workspaceId: string }) {
  const documents = useQuery(documentsQueryOptions(workspaceId))
  const chat = useInternalChat(workspaceId)
  const bottomRef = useRef<HTMLDivElement>(null)
  const latestTurn = chat.turns[chat.turns.length - 1]
  const scrollKey = latestTurn
    ? `${latestTurn.id}:${"text" in latestTurn ? latestTurn.text : ""}:${"status" in latestTurn ? latestTurn.status : ""}`
    : ""

  useEffect(() => {
    if (!scrollKey) {
      return
    }
    bottomRef.current?.scrollIntoView({ block: "end" })
  }, [scrollKey])

  if (documents.isPending) {
    return <Skeleton className="min-h-0 flex-1 rounded-xl" />
  }

  if (documents.isError) {
    return (
      <div className="rounded-xl border p-5">
        <p className="font-medium">Couldn't load documents</p>
        <p className="text-muted-foreground mt-1 text-sm">
          Something went wrong. Please try again.
        </p>
        <LoadingButton
          className="mt-3"
          loading={documents.isFetching}
          onClick={() => {
            void documents.refetch()
          }}
        >
          Retry
        </LoadingButton>
      </div>
    )
  }

  const rows = documents.data.data
  if (rows.length === 0) {
    return (
      <div
        className="flex min-h-0 flex-1 flex-col items-center justify-center rounded-xl border px-4 py-16 text-center"
        data-testid="chat-empty"
      >
        <div className="bg-muted mb-4 rounded-full p-4">
          <MessageSquare className="text-muted-foreground size-8" />
        </div>
        <h2 className="text-lg font-semibold">No documents yet</h2>
        <p className="text-muted-foreground mt-1 max-w-md">
          Upload a document in Knowledge so the sandbox has something to answer
          from.
        </p>
        <Button asChild className="mt-4">
          <Link to="/dashboard/knowledge">Go to Knowledge</Link>
        </Button>
      </div>
    )
  }

  const hasActive = rows.some((row) => row.status === "active")
  const hasProcessing = rows.some((row) => row.status === "processing")
  const canSend =
    chat.draft.trim().length > 0 && !chat.busy && !chat.awaitingDecision

  return (
    <div className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-xl border">
      <div className="flex items-center justify-end border-b px-3 py-2">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={chat.newChat}
          disabled={
            chat.busy || chat.awaitingDecision || chat.turns.length === 0
          }
        >
          New chat
        </Button>
      </div>
      {hasProcessing && !hasActive ? (
        <p className="text-muted-foreground border-b px-4 py-3 text-sm">
          Your document is still processing. You can ask as soon as it is ready.
        </p>
      ) : null}
      <div
        className="min-h-0 flex-1 overflow-y-auto px-4 py-4"
        role="log"
        aria-label="Conversation"
        data-testid="chat-thread"
      >
        {chat.turns.length === 0 ? (
          <p className="text-muted-foreground py-8 text-center text-sm">
            Ask a question about this workspace.
          </p>
        ) : (
          <ol className="flex flex-col gap-4">
            {chat.turns.map((turn) => (
              <li key={turn.id}>
                <ChatTurnView turn={turn} onConfirm={chat.confirm} />
              </li>
            ))}
          </ol>
        )}
        <div ref={bottomRef} />
      </div>
      <form
        className="flex items-end gap-2 border-t p-4"
        onSubmit={(event) => {
          event.preventDefault()
          chat.send()
        }}
      >
        <label className="sr-only" htmlFor="chat-message">
          Message
        </label>
        <Textarea
          id="chat-message"
          data-testid="chat-input"
          value={chat.draft}
          placeholder={
            chat.awaitingDecision
              ? "Approve or reject the action above to continue."
              : "Ask about your documents"
          }
          rows={2}
          disabled={chat.busy || chat.awaitingDecision}
          className="field-sizing-fixed max-h-32 min-h-12 flex-1 resize-none"
          onChange={(event) => chat.setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (
              event.key === "Enter" &&
              !event.shiftKey &&
              !event.nativeEvent.isComposing
            ) {
              event.preventDefault()
              chat.send()
            }
          }}
        />
        <Button type="submit" data-testid="chat-send" disabled={!canSend}>
          Send
        </Button>
      </form>
    </div>
  )
}

function ChatTurnView({
  turn,
  onConfirm,
}: {
  turn: ChatTurn
  onConfirm: (cardId: string, decision: "approved" | "rejected") => void
}) {
  if (turn.kind === "user") {
    return (
      <div className="flex justify-end">
        <p className="bg-primary text-primary-foreground max-w-[85%] rounded-2xl px-4 py-2 text-sm whitespace-pre-wrap">
          {turn.text}
        </p>
      </div>
    )
  }
  if (turn.kind === "assistant") {
    return (
      <div className="flex justify-start">
        <p className="bg-muted max-w-[85%] rounded-2xl px-4 py-2 text-sm whitespace-pre-wrap">
          {turn.streaming && turn.text.length === 0 ? (
            <span data-testid="chat-pending">Thinking…</span>
          ) : (
            turn.text
          )}
        </p>
      </div>
    )
  }
  if (turn.kind === "error") {
    return (
      <p
        className="border-destructive/40 bg-destructive/10 text-destructive max-w-lg rounded-xl border px-4 py-3 text-sm"
        data-testid="chat-error"
      >
        {turn.text}
      </p>
    )
  }
  const deciding = turn.status === "approving" || turn.status === "rejecting"
  return (
    <section
      aria-label={turn.title || "Confirmation"}
      className="max-w-lg rounded-xl border p-4"
      data-testid="hitl-card"
    >
      <p className="font-medium">{turn.title}</p>
      <p className="text-muted-foreground mt-1 text-sm">{turn.summary}</p>
      {turn.status === "pending" || deciding ? (
        <div className="mt-4 flex gap-2">
          <LoadingButton
            type="button"
            loading={turn.status === "approving"}
            disabled={turn.status !== "pending"}
            data-testid="hitl-approve"
            onClick={() => onConfirm(turn.id, "approved")}
          >
            Approve
          </LoadingButton>
          <LoadingButton
            type="button"
            variant="outline"
            loading={turn.status === "rejecting"}
            disabled={turn.status !== "pending"}
            data-testid="hitl-reject"
            onClick={() => onConfirm(turn.id, "rejected")}
          >
            Reject
          </LoadingButton>
        </div>
      ) : turn.status === "approved" || turn.status === "rejected" ? (
        <p className="text-muted-foreground mt-4 text-sm">
          {turn.status === "approved" ? "Approved" : "Rejected"}
        </p>
      ) : null}
    </section>
  )
}
