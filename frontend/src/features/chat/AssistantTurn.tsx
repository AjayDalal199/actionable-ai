import { Sparkles } from "lucide-react"
import { useEffect, useLayoutEffect, useRef, useState } from "react"

import { MarkdownMessage } from "@/features/chat/MarkdownMessage"

/**
 * SSE chunks often arrive together, so paint the reply on a short cadence
 * instead of showing the whole answer in one frame.
 */
function revealPace(behind: number): { wait: number; step: number } {
  if (behind > 80) {
    return { wait: 16, step: 5 }
  }
  if (behind > 12) {
    return { wait: 16, step: 2 }
  }
  return { wait: 32, step: 1 }
}

function useRevealedText(text: string, streaming: boolean): string {
  const textRef = useRef(text)
  const streamingRef = useRef(streaming)
  textRef.current = text
  streamingRef.current = streaming
  const countRef = useRef(0)
  const [count, setCount] = useState(0)

  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)")
    let frame = 0
    let last = 0

    const tick = (now: number) => {
      const target = textRef.current.length
      if (countRef.current > target || media.matches) {
        if (countRef.current !== target) {
          countRef.current = target
          setCount(target)
        }
      } else if (countRef.current < target) {
        const behind = target - countRef.current
        const { wait, step } = revealPace(behind)
        if (now - last >= wait) {
          countRef.current = Math.min(target, countRef.current + step)
          setCount(countRef.current)
          last = now
        }
      }

      const caughtUp = countRef.current >= textRef.current.length
      if (streamingRef.current || !caughtUp) {
        frame = requestAnimationFrame(tick)
      }
    }

    frame = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frame)
  }, [])

  return text.slice(0, Math.min(count, text.length))
}

function ThinkingDots() {
  return (
    <span
      className="chat-thinking-dots inline-flex items-center gap-1"
      aria-hidden="true"
    >
      <span className="chat-thinking-dot bg-primary size-1.5 rounded-full" />
      <span className="chat-thinking-dot bg-primary size-1.5 rounded-full" />
      <span className="chat-thinking-dot bg-primary size-1.5 rounded-full" />
    </span>
  )
}

function ThinkingIndicator() {
  return (
    <span
      className="inline-flex items-center gap-2.5 py-0.5"
      data-testid="chat-pending"
      role="status"
    >
      <Sparkles
        aria-hidden="true"
        className="text-primary size-3.5 shrink-0 animate-pulse motion-reduce:animate-none"
      />
      <span className="chat-thinking-label text-sm font-medium">Thinking</span>
      <ThinkingDots />
    </span>
  )
}

function StreamCaret() {
  return (
    <span
      className="chat-caret bg-primary ml-0.5 inline-block h-[1.05em] w-0.5 translate-y-px align-[-0.12em]"
      aria-hidden="true"
    />
  )
}

export function AssistantTurn({
  text,
  streaming,
}: {
  text: string
  streaming: boolean
}) {
  const revealed = useRevealedText(text, streaming)
  const rootRef = useRef<HTMLDivElement>(null)
  const thinking = revealed.length === 0
  const live = streaming || revealed.length < text.length

  useLayoutEffect(() => {
    if (revealed.length === 0) {
      return
    }
    const thread = rootRef.current?.closest("[data-testid='chat-thread']")
    thread?.lastElementChild?.scrollIntoView({ block: "end" })
  }, [revealed])

  return (
    <div className="flex justify-start" ref={rootRef}>
      <div
        className="bg-muted max-w-[min(85%,42rem)] rounded-2xl px-4 py-3 text-sm leading-6 wrap-break-word"
        aria-busy={live}
      >
        {thinking ? (
          <ThinkingIndicator />
        ) : (
          <div className="chat-markdown">
            <MarkdownMessage text={revealed} live={live} />
            {live ? <StreamCaret /> : null}
          </div>
        )}
      </div>
    </div>
  )
}
