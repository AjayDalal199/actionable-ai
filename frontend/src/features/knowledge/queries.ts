import { queryOptions } from "@tanstack/react-query"

import { KnowledgeService } from "@/api"

export const documentKeys = {
  all: ["knowledge", "documents"] as const,
}

export function documentsQueryOptions(workspaceId: string) {
  return queryOptions({
    queryKey: [...documentKeys.all, workspaceId] as const,
    queryFn: async () =>
      (
        await KnowledgeService.readDocuments({
          query: { skip: 0, limit: 100 },
        })
      ).data,
    refetchInterval: (query) => {
      const documents = query.state.data?.data ?? []
      const stillProcessing = documents.some(
        (document) => document.status === "processing",
      )
      return stillProcessing ? 2000 : false
    },
  })
}
