import { destroyWidget, mountWidget, type WidgetConfig } from "./element"
import { registerTool, type ToolFn } from "./tools"

export type { ToolFn }
export { registerTool }
export { destroyWidget as destroy }

type InitOptions = {
  workspace: string
  token?: string | null
  apiBase?: string
}

const script = document.currentScript
const scriptOrigin = originOf(script)

export function init(options: InitOptions) {
  const workspace = options.workspace.trim()
  if (!workspace) return
  const config: WidgetConfig = {
    workspace,
    token: options.token?.trim() || null,
    apiBase: (options.apiBase ?? scriptOrigin).replace(/\/$/, ""),
  }
  mountWidget(config)
}

function originOf(node: Element | null) {
  if (node instanceof HTMLScriptElement && node.src) {
    try {
      return new URL(node.src).origin
    } catch {
      return window.location.origin
    }
  }
  return window.location.origin
}

if (script instanceof HTMLScriptElement && script.dataset.workspace) {
  init({
    workspace: script.dataset.workspace,
    token: script.dataset.token,
    apiBase: script.dataset.apiBase,
  })
}
