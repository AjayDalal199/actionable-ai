import { createFileRoute } from "@tanstack/react-router"

import { LegalLayout } from "@/features/marketing/LegalLayout"

export const Route = createFileRoute("/terms")({
  component: TermsPage,
  head: () => ({
    meta: [{ title: "Terms of Service — Actionable AI" }],
  }),
})

function TermsPage() {
  return (
    <LegalLayout title="Terms of Service">
      <p>Last updated: August 23, 2026</p>
      <p>
        Actionable AI provides software that lets you embed an agent in your
        product, retrieve from knowledge you upload, and call tools you
        register. By creating an account you agree to use the service lawfully
        and to keep your credentials and signed user tokens under your control.
      </p>
      <p>
        You are responsible for the APIs, documents, and user context you
        connect. Write tools execute only after an end-user confirms in the
        widget; that confirmation does not replace your own authorization
        checks.
      </p>
      <p>
        The service is provided as-is. We may suspend accounts that abuse the
        platform, attempt to bypass confirmation gates, or violate these terms.
        For questions, contact{" "}
        <a
          href="mailto:hello@actionable.ai"
          className="text-primary underline-offset-4 hover:underline"
        >
          hello@actionable.ai
        </a>
        .
      </p>
    </LegalLayout>
  )
}
