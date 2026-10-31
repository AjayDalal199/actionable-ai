const LOOPBACK_HOSTS = new Set(["localhost", "127.0.0.1", "::1"])

export const TOOL_NAME_PATTERN = /^[a-z0-9_]+$/

export const TOOL_NAME_MAX = 128

export const TOOL_NAME_MESSAGE = "Tool names must be snake_case with no spaces."

export const TOOL_URL_MESSAGE =
  "URL must use HTTPS. HTTP is allowed only for localhost."

export const TOOL_SCHEMA_MESSAGE =
  "Schema must be a JSON object with type and properties."

export const TOOL_JSON_MESSAGE = "Enter valid JSON."

export const WRITE_HITL_REASON =
  "Destructive API methods (POST, PUT, DELETE) strictly require user confirmation for safety."

export const DEFAULT_SCHEMA_TEXT = `{
  "type": "object",
  "properties": {}
}`

const WRITE_METHODS = new Set(["POST", "PUT", "DELETE"])

export function isWriteMethod(method: string): boolean {
  return WRITE_METHODS.has(method)
}

export function toolNameError(name: string): string | null {
  if (name.length > TOOL_NAME_MAX || !TOOL_NAME_PATTERN.test(name)) {
    return TOOL_NAME_MESSAGE
  }
  return null
}

export function toolUrlError(url: string): string | null {
  const cleaned = url.trim()
  if (!cleaned || cleaned.length > 2048 || /\s/.test(cleaned)) {
    return TOOL_URL_MESSAGE
  }
  let parsed: URL
  try {
    parsed = new URL(cleaned)
  } catch {
    return TOOL_URL_MESSAGE
  }
  const host = parsed.hostname
    .toLowerCase()
    .replace(/^\[|\]$/g, "")
    .replace(/\.+$/, "")
  if (parsed.protocol === "https:" && host) {
    return null
  }
  if (parsed.protocol === "http:" && LOOPBACK_HOSTS.has(host)) {
    return null
  }
  return TOOL_URL_MESSAGE
}

export function parseToolSchema(
  text: string,
):
  | { ok: true; value: Record<string, unknown> }
  | { ok: false; message: string } {
  let value: unknown
  try {
    value = JSON.parse(text)
  } catch {
    return { ok: false, message: TOOL_JSON_MESSAGE }
  }
  if (!isSchemaObject(value)) {
    return { ok: false, message: TOOL_SCHEMA_MESSAGE }
  }
  return { ok: true, value }
}

function isSchemaObject(value: unknown): value is Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return false
  }
  const record = value as Record<string, unknown>
  const properties = record.properties
  return (
    record.type === "object" &&
    typeof properties === "object" &&
    properties !== null &&
    !Array.isArray(properties)
  )
}
