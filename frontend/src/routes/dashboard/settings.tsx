import { createFileRoute } from "@tanstack/react-router"

import { SettingsPage } from "@/features/settings/SettingsPage"

export const Route = createFileRoute("/dashboard/settings")({
  component: SettingsPage,
  head: () => ({
    meta: [
      {
        title: "Settings — Actionable AI",
      },
    ],
  }),
})
