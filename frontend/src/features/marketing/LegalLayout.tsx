import type { ReactNode } from "react"

import { LandingFooter } from "@/features/marketing/LandingFooter"
import { LandingHeader } from "@/features/marketing/LandingHeader"

interface LegalLayoutProps {
  title: string
  children: ReactNode
}

export function LegalLayout({ title, children }: LegalLayoutProps) {
  return (
    <div className="flex min-h-svh flex-col">
      <LandingHeader />
      <main className="page-content flex-1 py-16">
        <article className="max-w-[65ch]">
          <h1 className="text-section">{title}</h1>
          <div className="text-muted-foreground mt-8 flex flex-col gap-4 text-base leading-relaxed">
            {children}
          </div>
        </article>
      </main>
      <LandingFooter />
    </div>
  )
}
