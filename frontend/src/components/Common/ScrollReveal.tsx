import { useEffect, useRef } from "react"
import { cn } from "@/lib/utils"

interface ScrollRevealProps extends React.HTMLAttributes<HTMLDivElement> {}

const supportsScrollTimeline =
  typeof window !== "undefined" &&
  typeof CSS !== "undefined" &&
  CSS.supports?.("(animation-timeline: view()) and (animation-range: entry)")

let sharedObserver: IntersectionObserver | null = null

function getSharedObserver() {
  if (!sharedObserver && typeof window !== "undefined") {
    sharedObserver = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-revealed")
            sharedObserver?.unobserve(entry.target)
          }
        }
      },
      { threshold: 0.1, rootMargin: "0px 0px -50px 0px" },
    )
  }
  return sharedObserver
}

export function ScrollReveal({
  className,
  children,
  ...props
}: ScrollRevealProps) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (supportsScrollTimeline) {
      return
    }

    const node = ref.current
    if (!node) return

    const observer = getSharedObserver()
    observer?.observe(node)

    return () => {
      observer?.unobserve(node)
    }
  }, [])

  return (
    <div ref={ref} className={cn("scroll-reveal", className)} {...props}>
      {children}
    </div>
  )
}
