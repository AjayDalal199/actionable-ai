const ALLOWED_EXTENSIONS = new Set([".pdf", ".md", ".markdown", ".txt"])

export const MAX_UPLOAD_BYTES = 10 * 1024 * 1024

export const UNSUPPORTED_FILE_MESSAGE =
  "Unsupported file type. Only PDF, Markdown, and text files are supported."

export const FILE_TOO_LARGE_MESSAGE = "File exceeds 10MB limit."

export const EMPTY_FILE_MESSAGE = "File is empty."

export const UPLOAD_INTERRUPTED_MESSAGE =
  "Upload interrupted. Please try again."

export function fileRejection(file: File): string | null {
  const extension = extensionOf(file.name)
  if (!ALLOWED_EXTENSIONS.has(extension)) {
    return UNSUPPORTED_FILE_MESSAGE
  }
  if (file.size === 0) {
    return EMPTY_FILE_MESSAGE
  }
  if (file.size > MAX_UPLOAD_BYTES) {
    return FILE_TOO_LARGE_MESSAGE
  }
  return null
}

function extensionOf(filename: string): string {
  const dot = filename.lastIndexOf(".")
  if (dot <= 0) {
    return ""
  }
  return filename.slice(dot).toLowerCase()
}
