import type { Components } from "react-markdown"
import ReactMarkdown from "react-markdown"
import remarkBreaks from "remark-breaks"
import remarkGfm from "remark-gfm"

/**
 * Close markers that are still open so a partial reply does not flash raw
 * `**` while the rest of the token is arriving.
 */
function balanceLiveMarkdown(source: string): string {
  let text = source
  const fenceCount = text.match(/```/g)?.length ?? 0
  if (fenceCount % 2 === 1) {
    text += text.endsWith("\n") ? "```" : "\n```"
  }

  const withoutFences = text.replace(/```[\s\S]*?```/g, "")
  const tickCount = withoutFences.match(/`/g)?.length ?? 0
  const openTick =
    tickCount % 2 === 1 ? withoutFences.lastIndexOf("`") : withoutFences.length
  const plain =
    openTick === withoutFences.length
      ? withoutFences.replace(/`[^`\n]*`/g, "")
      : withoutFences.slice(0, openTick)

  if ((plain.match(/\*\*/g)?.length ?? 0) % 2 === 1) {
    text += "**"
  }
  if ((plain.match(/__/g)?.length ?? 0) % 2 === 1) {
    text += "__"
  }
  if ((plain.match(/~~/g)?.length ?? 0) % 2 === 1) {
    text += "~~"
  }
  if (tickCount % 2 === 1) {
    text += "`"
  }
  return text
}

const components: Components = {
  h1: ({ children }) => (
    <h2 className="text-base font-semibold tracking-tight">{children}</h2>
  ),
  h2: ({ children }) => (
    <h3 className="text-sm font-semibold tracking-tight">{children}</h3>
  ),
  h3: ({ children }) => <h4 className="text-sm font-semibold">{children}</h4>,
  h4: ({ children }) => <h5 className="text-sm font-medium">{children}</h5>,
  p: ({ children }) => <p>{children}</p>,
  ul: ({ children }) => (
    <ul className="list-disc space-y-1 pl-5">{children}</ul>
  ),
  ol: ({ children }) => (
    <ol className="list-decimal space-y-1 pl-5">{children}</ol>
  ),
  li: ({ children }) => (
    <li className="pl-0.5 [&_p]:m-0 [&_p]:inline">{children}</li>
  ),
  a: ({ href, children }) => {
    if (!href) {
      return <span>{children}</span>
    }
    return (
      <a
        href={href}
        target="_blank"
        rel="noreferrer noopener"
        className="text-primary decoration-primary/40 underline underline-offset-2"
      >
        {children}
      </a>
    )
  },
  blockquote: ({ children }) => (
    <blockquote className="border-primary/50 text-muted-foreground border-l-2 pl-3">
      {children}
    </blockquote>
  ),
  pre: ({ children }) => (
    <pre className="bg-background/80 overflow-x-auto rounded-lg px-3 py-2 font-mono text-[0.8125rem] leading-5">
      {children}
    </pre>
  ),
  code: ({ className, children }) => (
    <code className={className}>{children}</code>
  ),
  hr: () => <hr className="border-border" />,
  table: ({ children }) => (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-left">{children}</table>
    </div>
  ),
  th: ({ children }) => (
    <th className="border-border border-b px-2 py-1 font-medium">{children}</th>
  ),
  td: ({ children }) => (
    <td className="border-border border-b px-2 py-1 align-top">{children}</td>
  ),
  input: ({ type, checked }) => {
    if (type !== "checkbox") {
      return null
    }
    return (
      <input
        type="checkbox"
        checked={Boolean(checked)}
        disabled
        className="accent-primary mr-1.5 align-middle"
      />
    )
  },
  img: ({ src, alt }) => {
    if (!src) {
      return null
    }
    return (
      <img
        src={src}
        alt={alt ?? ""}
        className="max-h-64 max-w-full rounded-lg"
      />
    )
  },
}

export function MarkdownMessage({
  text,
  live,
}: {
  text: string
  live: boolean
}) {
  const source = live ? balanceLiveMarkdown(text) : text
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm, remarkBreaks]}
      components={components}
    >
      {source}
    </ReactMarkdown>
  )
}
