import { queryOptions } from "@tanstack/react-query"

import { UsersService } from "@/api"

export const authKeys = {
  currentUser: ["currentUser"] as const,
}

export const currentUserQueryOptions = queryOptions({
  queryKey: authKeys.currentUser,
  queryFn: async () => (await UsersService.readUserMe()).data,
})
