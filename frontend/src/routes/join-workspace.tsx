import { createFileRoute, redirect } from "@tanstack/react-router"
import { z } from "zod"

import { JoinWorkspace } from "@/features/workspace/JoinWorkspace"

const searchSchema = z.object({
  token: z.string().catch(""),
  decision: z.enum(["decline"]).optional().catch(undefined),
})

export const Route = createFileRoute("/join-workspace")({
  component: JoinWorkspacePage,
  validateSearch: searchSchema,
  beforeLoad: async ({ search }) => {
    if (!search.token) {
      throw redirect({ to: "/login" })
    }
  },
  head: () => ({
    meta: [
      {
        title: "Join workspace — Actionable AI",
      },
    ],
  }),
})

function JoinWorkspacePage() {
  const { token, decision } = Route.useSearch()
  return <JoinWorkspace token={token} decision={decision} />
}
