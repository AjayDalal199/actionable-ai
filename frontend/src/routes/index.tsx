import { createFileRoute, redirect } from "@tanstack/react-router"

import { isLoggedIn } from "@/features/auth/session"
import { LandingPage } from "@/features/marketing/LandingPage"

export const Route = createFileRoute("/")({
  beforeLoad: async () => {
    if (isLoggedIn()) {
      throw redirect({ to: "/dashboard" })
    }
  },
  component: LandingPage,
  head: () => ({
    meta: [
      { title: "Actionable AI — An agent that answers and acts" },
      {
        name: "description",
        content:
          "Embed an AI agent in your product. It answers from your docs, does the work, and asks a human to confirm the action first.",
      },
      {
        property: "og:title",
        content: "Actionable AI — An agent that answers and acts",
      },
      {
        property: "og:description",
        content:
          "Embed an AI agent in your product. It answers from your docs, does the work, and asks a human to confirm the action first.",
      },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
})
