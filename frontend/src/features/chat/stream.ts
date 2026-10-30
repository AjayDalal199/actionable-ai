import { jsonBodySerializer } from "@/api/client"
import { client } from "@/api/client.gen"

const BEARER = [{ scheme: "bearer" as const, type: "http" as const }]

export class ChatRequestError extends Error {
  readonly status: number | null

  constructor(status: number | null) {
    super("Chat request failed")
    this.name = "ChatRequestError"
    this.status = status
  }
}

export type ChatEvent =
  | { type: "message"; text: string }
  | {
      type: "hitl_required"
      pendingActionId: string
      title: string
      summary: string
    }
  | { type: "error"; message: string }
  | { type: "done" }

type ChatBody = {
  session_id: string
  message: string
  channel: "internal"
}

type ConfirmBody = {
  pending_action_id: string
  decision: "approved" | "rejected"
}

/**
 * Chat SSE is not in the generated client. These calls use that client's bearer.
 */
export function streamInternalChat(
  body: ChatBody,
  onEvent: (event: ChatEvent) => void,
  signal: AbortSignal,
) {
  return readChatEvents("/api/v1/chat/stream", body, onEvent, signal)
}

export function confirmInternalAction(
  body: ConfirmBody,
  onEvent: (event: ChatEvent) => void,
  signal: AbortSignal,
) {
  return readChatEvents("/api/v1/chat/hitl-confirm", body, onEvent, signal)
}

async function readChatEvents(
  url: "/api/v1/chat/stream" | "/api/v1/chat/hitl-confirm",
  body: ChatBody | ConfirmBody,
  onEvent: (event: ChatEvent) => void,
  signal: AbortSignal,
) {
  let failure: unknown
  let sawDone = false
  const { stream } = await client.sse.post({
    ...jsonBodySerializer,
    url,
    body,
    headers: {
      Accept: "text/event-stream",
      "Content-Type": "application/json",
    },
    security: BEARER,
    signal,
    sseMaxRetryAttempts: 1,
    onSseError: (error) => {
      failure = error
    },
    onSseEvent: (raw) => {
      const parsed = parseChatEvent(raw.event, raw.data)
      if (!parsed) {
        return
      }
      if (parsed.type === "done") {
        sawDone = true
      }
      onEvent(parsed)
    },
  })

  for await (const _chunk of stream) {
    if (signal.aborted) {
      break
    }
  }

  if (signal.aborted || isAbortError(failure)) {
    throw new DOMException("Aborted", "AbortError")
  }
  if (!sawDone) {
    throw toChatRequestError(failure)
  }
}

function parseChatEvent(
  name: string | undefined,
  data: unknown,
): ChatEvent | null {
  const record =
    typeof data === "object" && data !== null
      ? (data as Record<string, unknown>)
      : null
  if (name === "done") {
    return { type: "done" }
  }
  if (!record) {
    return null
  }
  if (name === "message" && typeof record.text === "string") {
    return { type: "message", text: record.text }
  }
  if (name === "hitl_required") {
    const pendingActionId = record.pending_action_id
    const title = record.title
    const summary = record.summary
    if (
      typeof pendingActionId !== "string" ||
      typeof title !== "string" ||
      typeof summary !== "string"
    ) {
      return null
    }
    return { type: "hitl_required", pendingActionId, title, summary }
  }
  if (name === "error" && typeof record.message === "string") {
    return { type: "error", message: record.message }
  }
  return null
}

function toChatRequestError(error: unknown): ChatRequestError {
  if (error instanceof ChatRequestError) {
    return error
  }
  const message = error instanceof Error ? error.message : ""
  const match = /SSE failed: (\d{3})/.exec(message)
  return new ChatRequestError(match ? Number(match[1]) : null)
}

function isAbortError(error: unknown): boolean {
  return error instanceof Error && error.name === "AbortError"
}
