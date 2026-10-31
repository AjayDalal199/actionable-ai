export type WidgetEvent =
  | { type: "message"; text: string }
  | { type: "hitl_required"; pendingActionId: string; title: string; summary: string }
  | { type: "tool_js"; callId: string; name: string; arguments: Record<string, unknown> }
  | { type: "notice"; message: string }
  | { type: "error"; message: string }
  | { type: "done" }

const CONNECTION = "Connection lost. Please try again."

export async function postEvents(
  url: string,
  body: unknown,
  token: string | null,
  onEvent: (event: WidgetEvent) => void,
  signal: AbortSignal,
) {
  const headers: Record<string, string> = {
    Accept: "text/event-stream",
    "Content-Type": "application/json",
  }
  if (token) headers.Authorization = `Bearer ${token}`
  const response = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
    signal,
    credentials: "omit",
  })
  if (!response.ok || !response.body) {
    throw new Error(await errorMessage(response))
  }
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    buffer = drain(buffer, onEvent)
  }
  drain(`${buffer}\n\n`, onEvent)
}

export function failureCopy(error: unknown, signal: AbortSignal) {
  if (
    signal.aborted &&
    signal.reason instanceof DOMException &&
    signal.reason.name === "TimeoutError"
  ) {
    return "I'm having trouble connecting to my brain right now. Please try again."
  }
  if (error instanceof TypeError) return CONNECTION
  if (error instanceof Error && error.message && error.name !== "AbortError") {
    return error.message
  }
  return CONNECTION
}

async function errorMessage(response: Response) {
  try {
    const body = (await response.json()) as { detail?: unknown }
    if (typeof body.detail === "string" && body.detail.trim()) return body.detail
  } catch {
    // The body was not JSON.
  }
  return CONNECTION
}

function drain(buffer: string, onEvent: (event: WidgetEvent) => void) {
  const chunks = buffer.split(/\n\n/)
  const rest = chunks.pop() ?? ""
  for (const chunk of chunks) {
    const event = parseFrame(chunk)
    if (event) onEvent(event)
  }
  return rest
}

function parseFrame(frame: string): WidgetEvent | null {
  let name = "message"
  const data: string[] = []
  for (const line of frame.split("\n")) {
    if (line.startsWith("event:")) name = line.slice(6).trim()
    else if (line.startsWith("data:")) data.push(line.slice(5).trim())
  }
  if (data.length === 0) return null
  let payload: unknown
  try {
    payload = JSON.parse(data.join("\n"))
  } catch {
    return null
  }
  if (!payload || typeof payload !== "object") return null
  const record = payload as Record<string, unknown>
  if (name === "message" && typeof record.text === "string") {
    return { type: "message", text: record.text }
  }
  if (name === "hitl_required" && typeof record.pending_action_id === "string") {
    return {
      type: "hitl_required",
      pendingActionId: record.pending_action_id,
      title: typeof record.title === "string" ? record.title : "Please confirm",
      summary: typeof record.summary === "string" ? record.summary : "",
    }
  }
  if (
    name === "tool_js" &&
    typeof record.call_id === "string" &&
    typeof record.name === "string"
  ) {
    const args = record.arguments
    return {
      type: "tool_js",
      callId: record.call_id,
      name: record.name,
      arguments:
        args && typeof args === "object" && !Array.isArray(args)
          ? (args as Record<string, unknown>)
          : {},
    }
  }
  if (name === "notice" && typeof record.message === "string") {
    return { type: "notice", message: record.message }
  }
  if (name === "error") {
    const message = typeof record.message === "string" ? record.message : CONNECTION
    return { type: "error", message }
  }
  if (name === "done") return { type: "done" }
  return null
}
