import { useSuspenseQuery } from "@tanstack/react-query"
import { Search } from "lucide-react"
import { Suspense } from "react"

import { AddItem } from "@/features/items/AddItem"
import { columns } from "@/features/items/columns"
import { PendingItems } from "@/features/items/PendingItems"
import { itemsQueryOptions } from "@/features/items/queries"
import { DataTable } from "@/shared/components/DataTable"

function ItemsTableContent() {
  const { data: items } = useSuspenseQuery(itemsQueryOptions)

  if (items.data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="bg-muted mb-4 rounded-full p-4">
          <Search className="text-muted-foreground h-8 w-8" />
        </div>
        <h3 className="text-lg font-semibold">You don't have any items yet</h3>
        <p className="text-muted-foreground">Add a new item to get started</p>
      </div>
    )
  }

  return <DataTable columns={columns} data={items.data} />
}

export function ItemsPage() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Items</h1>
          <p className="text-muted-foreground">Create and manage your items</p>
        </div>
        <AddItem />
      </div>
      <Suspense fallback={<PendingItems />}>
        <ItemsTableContent />
      </Suspense>
    </div>
  )
}
