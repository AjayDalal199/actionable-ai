import DOMPurify from "dompurify"
import { marked } from "marked"

marked.setOptions({ async: false, gfm: true, breaks: true })

export function renderMarkdown(source: string) {
  const html = marked.parse(source, { async: false }) as string
  return DOMPurify.sanitize(html)
}
