import { Link } from "@tanstack/react-router"
import { Zap } from "lucide-react"

import { cn } from "@/shared/lib/utils"

interface LogoProps {
  variant?: "full" | "icon" | "responsive"
  className?: string
  asLink?: boolean
  to?: "/" | "/dashboard"
}

export function Logo({
  variant = "full",
  className,
  asLink = true,
  to = "/dashboard",
}: LogoProps) {
  const showWordmark = variant === "full" || variant === "responsive"

  const content = (
    <span className={cn("inline-flex items-center gap-2", className)}>
      <span
        className={cn(
          "bg-primary text-primary-foreground flex shrink-0 items-center justify-center rounded-md",
          variant === "icon" ? "size-6" : "size-8",
        )}
      >
        <Zap className={variant === "icon" ? "size-3.5" : "size-4"} />
      </span>
      {showWordmark && (
        <span
          className={cn(
            "text-foreground text-base font-semibold tracking-tight",
            variant === "responsive" && "group-data-[collapsible=icon]:hidden",
          )}
        >
          Actionable AI
        </span>
      )}
    </span>
  )

  if (!asLink) {
    return content
  }

  return <Link to={to}>{content}</Link>
}
