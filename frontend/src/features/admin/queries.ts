import { queryOptions } from "@tanstack/react-query"
import { redirect } from "@tanstack/react-router"

import { UsersService } from "@/api"

export const userKeys = {
  all: ["users"] as const,
}

export const usersQueryOptions = queryOptions({
  queryKey: userKeys.all,
  queryFn: async () =>
    (await UsersService.readUsers({ query: { skip: 0, limit: 100 } })).data,
})

export async function assertSuperuser() {
  const { data: user } = await UsersService.readUserMe()
  if (!user.is_superuser) {
    throw redirect({ to: "/dashboard" })
  }
}
