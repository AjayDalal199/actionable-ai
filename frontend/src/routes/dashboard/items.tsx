import { createFileRoute } from "@tanstack/react-router"

import { ItemsPage } from "@/features/items/ItemsPage"
import { itemsQueryOptions } from "@/features/items/queries"

export const Route = createFileRoute("/dashboard/items")({
  component: ItemsPage,
  loader: ({ context }) =>
    context.queryClient.ensureQueryData(itemsQueryOptions),
  head: () => ({
    meta: [
      {
        title: "Items — Actionable AI",
      },
    ],
  }),
})
