import { createFileRoute } from "@tanstack/react-router"

import { LegalLayout } from "@/features/marketing/LegalLayout"

export const Route = createFileRoute("/privacy")({
  component: PrivacyPage,
  head: () => ({
    meta: [{ title: "Privacy Policy — Actionable AI" }],
  }),
})

function PrivacyPage() {
  return (
    <LegalLayout title="Privacy Policy">
      <p>Last updated: August 23, 2026</p>
      <p>
        We collect account information you submit (name, email) and the
        knowledge, tool schemas, and chat traffic you send through the platform
        so the agent can retrieve and act. Signed user context is used to
        authorize tool calls; we do not invent permissions on your backend.
      </p>
      <p>
        Workspace data is processed to provide the service: embedding uploaded
        documents, routing model calls, and logging tool confirmations. We do
        not sell this data. Operators with access to a workspace can see the
        queries and actions that workspace produces.
      </p>
      <p>
        You can request account deletion from settings once signed in, or by
        writing to{" "}
        <a
          href="mailto:hello@actionable.ai"
          className="text-primary underline-offset-4 hover:underline"
        >
          hello@actionable.ai
        </a>
        . This notice will expand as we add processors, retention windows, and
        regional details.
      </p>
    </LegalLayout>
  )
}
