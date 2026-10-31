import { renderMarkdown } from "./markdown"
import { failureCopy, postEvents, type WidgetEvent } from "./sse"
import { styles } from "./styles"
import { toolFor } from "./tools"

const MAX_CHARS = 2000
const TIMEOUT_MS = 45_000
const FALLBACK = "I couldn't run that on this page."

type HitlState = "open" | "approved" | "rejected"

type HitlCard = {
  id: string
  title: string
  summary: string
  state: HitlState
}

type Message = {
  id: number
  role: "user" | "assistant"
  text: string
  hitl?: HitlCard
}

type ToolCall = {
  callId: string
  name: string
  arguments: Record<string, unknown>
}

export type WidgetConfig = {
  workspace: string
  token: string | null
  apiBase: string
}

export class A2IWidget extends HTMLElement {
  private root!: ShadowRoot
  private logEl!: HTMLElement
  private bannerEl!: HTMLElement
  private panelEl!: HTMLElement
  private fabEl!: HTMLButtonElement
  private inputEl!: HTMLTextAreaElement
  private sendEl!: HTMLButtonElement
  private messages: Message[] = [
    { id: 0, role: "assistant", text: "Hello! How can I help?" },
  ]
  private nextId = 1
  private busy = false
  private open = false
  private notice = ""
  private sessionId = crypto.randomUUID()
  private config: WidgetConfig = { workspace: "", token: null, apiBase: "" }
  private hideTimer = 0

  connectedCallback() {
    if (this.shadowRoot) return
    this.root = this.attachShadow({ mode: "open" })
    this.root.innerHTML = `<style>${styles}</style>
      <button class="fab" type="button" aria-label="Open chat" aria-expanded="false">Chat</button>
      <section class="panel" aria-hidden="true">
        <header>
          <strong>Actionable AI</strong>
          <button class="close" type="button" aria-label="Close">×</button>
        </header>
        <p class="banner" hidden></p>
        <div class="log" role="log" aria-live="polite"></div>
        <form>
          <textarea rows="1" maxlength="${MAX_CHARS}" placeholder="Ask me anything or ask me to do something..."></textarea>
          <button class="send" type="submit">Send</button>
        </form>
      </section>`
    this.fabEl = this.root.querySelector(".fab") as HTMLButtonElement
    this.panelEl = this.root.querySelector(".panel") as HTMLElement
    this.bannerEl = this.root.querySelector(".banner") as HTMLElement
    this.logEl = this.root.querySelector(".log") as HTMLElement
    this.inputEl = this.root.querySelector("textarea") as HTMLTextAreaElement
    this.sendEl = this.root.querySelector(".send") as HTMLButtonElement
    this.fabEl.addEventListener("click", () => this.setOpen(true))
    this.root.querySelector(".close")?.addEventListener("click", () => this.setOpen(false))
    this.root.querySelector("form")?.addEventListener("submit", (event) => {
      event.preventDefault()
      void this.send()
    })
    this.inputEl.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault()
        void this.send()
      }
    })
    this.inputEl.addEventListener("input", () => {
      if (this.inputEl.value.length > MAX_CHARS) {
        this.inputEl.value = this.inputEl.value.slice(0, MAX_CHARS)
      }
    })
    this.render()
  }

  configure(config: WidgetConfig) {
    this.config = config
    this.sessionId = crypto.randomUUID()
    this.messages = [{ id: 0, role: "assistant", text: "Hello! How can I help?" }]
    this.nextId = 1
    this.notice = ""
    this.busy = false
    if (this.logEl) this.render()
  }

  private setOpen(next: boolean) {
    window.clearTimeout(this.hideTimer)
    if (next) {
      this.open = true
      this.panelEl.classList.remove("closing")
      this.panelEl.classList.add("open")
      this.panelEl.setAttribute("aria-hidden", "false")
      this.fabEl.hidden = true
      this.fabEl.setAttribute("aria-expanded", "true")
      this.lockPage(true)
      this.inputEl.focus()
      return
    }
    this.panelEl.classList.remove("open")
    this.panelEl.classList.add("closing")
    this.lockPage(false)
    this.hideTimer = window.setTimeout(() => {
      this.open = false
      this.panelEl.classList.remove("closing")
      this.panelEl.setAttribute("aria-hidden", "true")
      this.fabEl.hidden = false
      this.fabEl.setAttribute("aria-expanded", "false")
    }, 300)
  }

  private lockPage(lock: boolean) {
    if (!window.matchMedia("(max-width: 640px)").matches) return
    document.documentElement.style.overflow = lock ? "hidden" : ""
  }

  private async send() {
    const text = this.inputEl.value.trim().slice(0, MAX_CHARS)
    if (!text || this.busy || !this.config.workspace) return
    this.inputEl.value = ""
    this.messages.push({ id: this.nextId++, role: "user", text })
    const assistant: Message = { id: this.nextId++, role: "assistant", text: "" }
    this.messages.push(assistant)
    await this.converse(`/api/v1/widget/chat/stream`, {
      session_id: this.sessionId,
      message: text,
      workspace_key: this.config.workspace,
    }, assistant)
  }

  private async confirm(card: HitlCard, decision: "approved" | "rejected") {
    if (card.state !== "open" || this.busy) return
    card.state = decision
    this.render()
    const assistant: Message = { id: this.nextId++, role: "assistant", text: "" }
    this.messages.push(assistant)
    await this.converse(`/api/v1/widget/chat/hitl-confirm`, {
      pending_action_id: card.id,
      decision,
      workspace_key: this.config.workspace,
    }, assistant)
  }

  private async converse(path: string, body: unknown, assistant: Message) {
    this.busy = true
    this.render()
    const pendingTools: ToolCall[] = []
    const signal = AbortSignal.timeout(TIMEOUT_MS)
    try {
      await postEvents(
        `${this.config.apiBase}${path}`,
        body,
        this.config.token,
        (event) => {
          this.apply(event, assistant, pendingTools)
        },
        signal,
      )
      for (const call of pendingTools) {
        await this.runTool(call)
      }
    } catch (error) {
      if (!assistant.text) this.messages = this.messages.filter((item) => item !== assistant)
      this.messages.push({
        id: this.nextId++,
        role: "assistant",
        text: failureCopy(error, signal),
      })
    } finally {
      this.busy = false
      this.render()
      if (this.open) this.inputEl.focus()
    }
  }

  private apply(event: WidgetEvent, assistant: Message, pendingTools: ToolCall[]) {
    if (event.type === "notice") this.notice = event.message
    if (event.type === "message") assistant.text += event.text
    if (event.type === "error") assistant.text = event.message
    if (event.type === "hitl_required") {
      assistant.hitl = {
        id: event.pendingActionId,
        title: event.title,
        summary: event.summary,
        state: "open",
      }
    }
    if (event.type === "tool_js") pendingTools.push(event)
    this.render()
  }

  private async runTool(call: ToolCall) {
    const fn = toolFor(call.name)
    let ok = true
    let result: unknown = null
    let error: string | undefined
    if (!fn) {
      ok = false
      error = FALLBACK
      this.messages.push({ id: this.nextId++, role: "assistant", text: FALLBACK })
    } else {
      try {
        result = await fn(call.arguments)
      } catch {
        ok = false
        error = FALLBACK
        this.messages.push({ id: this.nextId++, role: "assistant", text: FALLBACK })
      }
    }
    const assistant: Message = { id: this.nextId++, role: "assistant", text: "" }
    this.messages.push(assistant)
    await this.converse(`/api/v1/widget/chat/tool-result`, {
      call_id: call.callId,
      workspace_key: this.config.workspace,
      ok,
      result: ok ? jsonValue(result) : null,
      error,
    }, assistant)
  }

  private render() {
    if (!this.logEl) return
    this.bannerEl.hidden = !this.notice
    this.bannerEl.textContent = this.notice
    this.inputEl.disabled = this.busy
    this.sendEl.disabled = this.busy
    this.logEl.replaceChildren()
    for (const message of this.messages) {
      if (!message.text && !message.hitl && !(this.busy && message === this.messages.at(-1))) {
        continue
      }
      if (message.text || (this.busy && message === this.messages.at(-1) && !message.hitl)) {
        const bubble = document.createElement("div")
        bubble.className = `bubble ${message.role}`
        if (message.role === "assistant" && message.text) {
          bubble.innerHTML = renderMarkdown(message.text)
        } else if (message.text) {
          bubble.textContent = message.text
        }
        if (this.busy && message === this.messages.at(-1) && !message.text) {
          bubble.append(loader())
        }
        this.logEl.append(bubble)
      }
      if (message.hitl) this.logEl.append(this.hitlCard(message.hitl))
    }
    this.logEl.scrollTop = this.logEl.scrollHeight
  }

  private hitlCard(card: HitlCard) {
    const region = document.createElement("div")
    region.className = "hitl"
    region.setAttribute("aria-live", "assertive")
    const title = document.createElement("h2")
    title.textContent = card.title
    const summary = document.createElement("p")
    summary.textContent = card.summary
    const actions = document.createElement("div")
    actions.className = "actions"
    const back = choice("Go back", false, card.state !== "open", () => {
      void this.confirm(card, "rejected")
    })
    const confirm = choice("Confirm", true, card.state !== "open", () => {
      void this.confirm(card, "approved")
    })
    actions.append(back, confirm)
    region.append(title, summary, actions)
    return region
  }
}

function choice(label: string, primary: boolean, disabled: boolean, onClick: () => void) {
  const button = document.createElement("button")
  button.type = "button"
  button.className = primary ? "choice primary" : "choice"
  button.textContent = label
  button.disabled = disabled
  button.addEventListener("click", onClick)
  return button
}

function loader() {
  const dots = document.createElement("div")
  dots.className = "dots"
  dots.setAttribute("aria-label", "Waiting for a reply")
  for (let index = 0; index < 3; index += 1) dots.append(document.createElement("span"))
  return dots
}

function jsonValue(value: unknown) {
  try {
    return JSON.parse(JSON.stringify(value ?? null)) as unknown
  } catch {
    return null
  }
}

if (!customElements.get("a2i-widget")) {
  customElements.define("a2i-widget", A2IWidget)
}

export function mountWidget(config: WidgetConfig) {
  const existing = document.querySelector("a2i-widget")
  const element = existing instanceof A2IWidget ? existing : new A2IWidget()
  if (element.parentElement === null) document.body.append(element)
  element.configure(config)
  return element
}

export function destroyWidget() {
  document.querySelector("a2i-widget")?.remove()
  document.documentElement.style.overflow = ""
}
