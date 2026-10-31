export type ToolFn = (args: Record<string, unknown>) => unknown

const tools = new Map<string, ToolFn>()

export function registerTool(name: string, fn: ToolFn) {
  if (!/^[a-z0-9_]+$/.test(name) || typeof fn !== "function") return
  tools.set(name, fn)
}

export function toolFor(name: string) {
  return tools.get(name)
}
