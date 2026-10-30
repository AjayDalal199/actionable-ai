import { queryOptions } from "@tanstack/react-query"

import { ToolsService } from "@/api"

export const toolKeys = {
  all: ["tools"] as const,
}

export function toolsQueryOptions(workspaceId: string) {
  return queryOptions({
    queryKey: [...toolKeys.all, workspaceId] as const,
    queryFn: async () =>
      (await ToolsService.readTools({ query: { skip: 0, limit: 100 } })).data,
  })
}
