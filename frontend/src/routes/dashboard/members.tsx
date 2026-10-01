import { createFileRoute } from "@tanstack/react-router"

import { MembersPage } from "@/features/workspace/MembersPage"

export const Route = createFileRoute("/dashboard/members")({
  component: MembersPage,
  head: () => ({
    meta: [
      {
        title: "Members — Actionable AI",
      },
    ],
  }),
})
