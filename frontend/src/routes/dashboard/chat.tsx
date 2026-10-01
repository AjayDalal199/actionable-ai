import { createFileRoute } from "@tanstack/react-router"

import { ChatPage } from "@/features/chat/ChatPage"

export const Route = createFileRoute("/dashboard/chat")({
  component: ChatPage,
  head: () => ({
    meta: [
      {
        title: "Chat — Actionable AI",
      },
    ],
  }),
})
