import { createFileRoute } from "@tanstack/react-router"

import { AdminPage } from "@/features/admin/AdminPage"
import { assertSuperuser, usersQueryOptions } from "@/features/admin/queries"

export const Route = createFileRoute("/dashboard/admin")({
  component: AdminPage,
  beforeLoad: async () => {
    await assertSuperuser()
  },
  loader: ({ context }) =>
    context.queryClient.ensureQueryData(usersQueryOptions),
  head: () => ({
    meta: [
      {
        title: "Admin — Actionable AI",
      },
    ],
  }),
})
