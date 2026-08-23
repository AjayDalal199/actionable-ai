import { FileText } from "lucide-react"
import type { ReactNode } from "react"

import { cn } from "@/shared/lib/utils"

function ArtifactFrame({
  label,
  children,
  className,
}: {
  label?: string
  children: ReactNode
  className?: string
}) {
  return (
    <div
      className={cn(
        "bg-card w-full overflow-hidden rounded-lg border",
        className,
      )}
    >
      {label ? (
        <div className="text-muted-foreground border-b px-4 py-2 font-mono text-[11px] tracking-wide uppercase">
          {label}
        </div>
      ) : null}
      <div className="p-4">{children}</div>
    </div>
  )
}

export function HitlCard({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "bg-card w-full rounded-lg border border-destructive/80 p-4",
        className,
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm font-medium">Cancel your Pro plan</p>
        <span className="bg-destructive shrink-0 rounded px-1.5 py-0.5 text-[11px] font-medium text-white">
          Cannot be undone
        </span>
      </div>
      <p className="text-muted-foreground mt-3 text-sm leading-relaxed">
        Your Pro plan will end. You keep access until this billing period
        closes.
      </p>
      <div className="mt-4 flex gap-2">
        <span className="bg-destructive inline-flex h-9 flex-1 items-center justify-center rounded-lg text-sm font-medium text-white">
          Go back
        </span>
        <span className="bg-primary text-primary-foreground inline-flex h-9 flex-1 items-center justify-center rounded-lg text-sm font-medium">
          Confirm
        </span>
      </div>
    </div>
  )
}

export function WidgetMock({ className }: { className?: string }) {
  return (
    <div
      role="img"
      aria-label="Chat widget asking the user to confirm canceling a Pro plan."
      className={cn(
        "bg-card w-full max-w-[360px] rounded-lg border",
        className,
      )}
    >
      <div className="flex items-center gap-2 border-b px-4 py-3">
        <span className="bg-primary size-1.5 rounded-full" />
        <span className="text-sm font-medium">Assistant</span>
      </div>
      <div className="flex flex-col gap-3 p-4">
        <p className="bg-primary text-primary-foreground ml-8 rounded-lg px-3 py-2 text-sm leading-relaxed">
          Cancel my Pro subscription.
        </p>
        <p className="bg-muted mr-8 rounded-lg px-3 py-2 text-sm leading-relaxed">
          I can cancel your Pro plan. This cannot be undone.
        </p>
        <HitlCard />
      </div>
      <div className="border-t p-3">
        <div className="text-muted-foreground rounded-lg border px-3 py-2 text-sm">
          Message…
        </div>
      </div>
    </div>
  )
}

export function FileListArtifact() {
  const files = [
    { name: "billing-policy.pdf", meta: "248 KB" },
    { name: "product-manual.md", meta: "64 KB" },
    { name: "openapi.yaml", meta: "12 KB" },
  ]
  return (
    <ArtifactFrame label="Knowledge">
      <ul className="flex flex-col gap-3">
        {files.map((file) => (
          <li key={file.name} className="flex items-center gap-3 text-sm">
            <FileText className="text-muted-foreground size-4 shrink-0" />
            <span className="min-w-0 flex-1 truncate font-mono text-[13px]">
              {file.name}
            </span>
            <span className="text-muted-foreground shrink-0 text-xs">
              {file.meta}
            </span>
          </li>
        ))}
      </ul>
    </ArtifactFrame>
  )
}

export function SchemaArtifact() {
  return (
    <ArtifactFrame label="Action">
      <pre className="overflow-x-auto font-mono text-[13px] leading-relaxed">
        {`{
  "name": "cancel_subscription",
  "write": true
}`}
      </pre>
    </ArtifactFrame>
  )
}

export function ScriptArtifact() {
  return (
    <ArtifactFrame label="Install">
      <pre className="overflow-x-auto font-mono text-[13px] leading-relaxed">
        {`<script
  src="https://cdn.actionable.ai/widget.js"
  data-workspace="ws_123"
></script>`}
      </pre>
    </ArtifactFrame>
  )
}
