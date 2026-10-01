import { queryOptions } from "@tanstack/react-query"

import { ItemsService } from "@/api"

export const itemKeys = {
  all: ["items"] as const,
}

export const itemsQueryOptions = queryOptions({
  queryKey: itemKeys.all,
  queryFn: async () =>
    (await ItemsService.readItems({ query: { skip: 0, limit: 100 } })).data,
})
