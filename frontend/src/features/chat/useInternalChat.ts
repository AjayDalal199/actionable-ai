import { useEffect, useRef, useState } from "react"

import { clearAccessToken } from "@/features/auth/session"
import {
  type ChatEvent,
  ChatRequestError,
  confirmInternalAction,
  streamInternalChat,
} from "@/features/chat/stream"

export type HitlStatus =
  | "pending"
  | "approving"
  | "rejecting"
  | "approved"
  | "rejected"
  | "closed"

export type ChatTurn =
  | { kind: "user"; id: string; text: string }
  | { kind: "assistant"; id: string; text: string; streaming: boolean }
  | {
      kind: "hitl"
      id: string
      pendingActionId: string
      title: string
      summary: string
      status: HitlStatus
    }
  | { kind: "error"; id: string; text: string }

const SESSION_PREFIX = "a2i.chat.session."

export function useInternalChat(workspaceId: string) {
  const [sessionId, setSessionId] = useState(() => chatSessionId(workspaceId))
  const [turns, setTurns] = useState<ChatTurn[]>([])
  const [draft, setDraft] = useState("")
  const [busy, setBusy] = useState(false)
  const busyRef = useRef(false)
  const requestRef = useRef(0)
  const abortRef = useRef<AbortController | null>(null)
  const assistantIdRef = useRef<string | null>(null)

  useEffect(() => {
    return () => {
      abortRef.current?.abort()
    }
  }, [])

  const awaitingDecision = turns.some(
    (turn) =>
      turn.kind === "hitl" &&
      (turn.status === "pending" ||
        turn.status === "approving" ||
        turn.status === "rejecting"),
  )

  const applyEvent = (event: ChatEvent, requestId: number) => {
    if (requestId !== requestRef.current) {
      return
    }
    if (event.type === "message") {
      if (!event.text) {
        return
      }
      const assistantId = assistantIdRef.current
      setTurns((current) =>
        current.map((turn) =>
          turn.kind === "assistant" && turn.id === assistantId
            ? { ...turn, text: turn.text + event.text }
            : turn,
        ),
      )
      return
    }
    if (event.type === "hitl_required") {
      const assistantId = assistantIdRef.current
      assistantIdRef.current = null
      setTurns((current) => [
        ...settleAssistant(current, assistantId),
        {
          kind: "hitl",
          id: crypto.randomUUID(),
          pendingActionId: event.pendingActionId,
          title: event.title,
          summary: event.summary,
          status: "pending",
        },
      ])
      return
    }
    if (event.type === "error") {
      const assistantId = assistantIdRef.current
      assistantIdRef.current = null
      setTurns((current) => [
        ...settleAssistant(current, assistantId),
        { kind: "error", id: crypto.randomUUID(), text: event.message },
      ])
      return
    }
    const assistantId = assistantIdRef.current
    assistantIdRef.current = null
    setTurns((current) => settleAssistant(current, assistantId))
  }

  const beginAssistant = () => {
    const assistantId = crypto.randomUUID()
    assistantIdRef.current = assistantId
    return assistantId
  }

  const failRequest = (
    requestId: number,
    error: unknown,
    kind: "turn" | "confirm",
    cardId?: string,
  ) => {
    if (requestId !== requestRef.current || isAbortError(error)) {
      return
    }
    if (error instanceof ChatRequestError && error.status === 401) {
      clearAccessToken()
      window.location.replace("/login")
      return
    }
    const assistantId = assistantIdRef.current
    assistantIdRef.current = null
    const closed = error instanceof ChatRequestError && error.status === 404
    setTurns((current) => [
      ...settleAssistant(current, assistantId).map((turn) => {
        if (turn.kind !== "hitl" || turn.id !== cardId) {
          return turn
        }
        if (closed) {
          return { ...turn, status: "closed" as const }
        }
        if (turn.status === "approving" || turn.status === "rejecting") {
          return { ...turn, status: "pending" as const }
        }
        return turn
      }),
      {
        kind: "error",
        id: crypto.randomUUID(),
        text: failureCopy(error, kind),
      },
    ])
  }

  const finishRequest = (requestId: number) => {
    if (requestId !== requestRef.current) {
      return
    }
    busyRef.current = false
    setBusy(false)
  }

  const send = () => {
    const message = draft.trim()
    if (!message || busyRef.current || awaitingDecision) {
      return
    }
    const requestId = ++requestRef.current
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller
    busyRef.current = true
    setBusy(true)
    setDraft("")
    const assistantId = beginAssistant()
    setTurns((current) => [
      ...current,
      { kind: "user", id: crypto.randomUUID(), text: message },
      { kind: "assistant", id: assistantId, text: "", streaming: true },
    ])
    void streamInternalChat(
      {
        session_id: sessionId,
        message,
        channel: "internal",
      },
      (event) => applyEvent(event, requestId),
      controller.signal,
    )
      .catch((error: unknown) => {
        failRequest(requestId, error, "turn")
      })
      .finally(() => {
        finishRequest(requestId)
      })
  }

  const confirm = (cardId: string, decision: "approved" | "rejected") => {
    const card = turns.find(
      (turn) => turn.kind === "hitl" && turn.id === cardId,
    )
    if (busyRef.current || card?.kind !== "hitl" || card.status !== "pending") {
      return
    }
    const requestId = ++requestRef.current
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller
    busyRef.current = true
    setBusy(true)
    const assistantId = beginAssistant()
    setTurns((current) => [
      ...current.map((turn) =>
        turn.kind === "hitl" && turn.id === cardId
          ? {
              ...turn,
              status:
                decision === "approved"
                  ? ("approving" as const)
                  : ("rejecting" as const),
            }
          : turn,
      ),
      { kind: "assistant", id: assistantId, text: "", streaming: true },
    ])
    void confirmInternalAction(
      { pending_action_id: card.pendingActionId, decision },
      (event) => applyEvent(event, requestId),
      controller.signal,
    )
      .then(() => {
        if (requestId !== requestRef.current) {
          return
        }
        setTurns((current) =>
          current.map((turn) =>
            turn.kind === "hitl" && turn.id === cardId
              ? {
                  ...turn,
                  status: decision === "approved" ? "approved" : "rejected",
                }
              : turn,
          ),
        )
      })
      .catch((error: unknown) => {
        failRequest(requestId, error, "confirm", cardId)
      })
      .finally(() => {
        finishRequest(requestId)
      })
  }

  const newChat = () => {
    if (busyRef.current || awaitingDecision) {
      return
    }
    requestRef.current += 1
    abortRef.current?.abort()
    const next = crypto.randomUUID()
    storeSession(workspaceId, next)
    setSessionId(next)
    setTurns([])
    setDraft("")
  }

  return {
    turns,
    draft,
    setDraft,
    busy,
    awaitingDecision,
    send,
    confirm,
    newChat,
  }
}

function settleAssistant(
  turns: ChatTurn[],
  assistantId: string | null,
): ChatTurn[] {
  if (!assistantId) {
    return turns
  }
  return turns.flatMap((turn) => {
    if (turn.kind !== "assistant" || turn.id !== assistantId) {
      return [turn]
    }
    if (!turn.text) {
      return []
    }
    return [{ ...turn, streaming: false }]
  })
}

function failureCopy(error: unknown, kind: "turn" | "confirm"): string {
  if (error instanceof ChatRequestError && error.status === 404) {
    return kind === "confirm"
      ? "That confirmation is no longer available."
      : "This conversation could not be resumed. Start a new chat and try again."
  }
  if (error instanceof ChatRequestError && error.status === 422) {
    return "That message could not be sent."
  }
  return "The assistant is unavailable right now."
}

function isAbortError(error: unknown): boolean {
  return error instanceof Error && error.name === "AbortError"
}

function chatSessionId(workspaceId: string): string {
  const existing = readSession(workspaceId)
  if (existing) {
    return existing
  }
  const created = crypto.randomUUID()
  storeSession(workspaceId, created)
  return created
}

function readSession(workspaceId: string): string | null {
  try {
    return sessionStorage.getItem(`${SESSION_PREFIX}${workspaceId}`)
  } catch {
    return null
  }
}

function storeSession(workspaceId: string, sessionId: string) {
  try {
    sessionStorage.setItem(`${SESSION_PREFIX}${workspaceId}`, sessionId)
  } catch {
    // Private mode can reject storage. The in-memory id still covers this visit.
  }
}
