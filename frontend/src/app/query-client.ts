import { MutationCache, QueryCache, QueryClient } from "@tanstack/react-query"
import { AxiosError } from "axios"

import { clearAccessToken } from "@/features/auth/session"

function handleApiError(error: Error) {
  if (
    error instanceof AxiosError &&
    [401, 403].includes(error.response?.status ?? 0)
  ) {
    clearAccessToken()
    window.location.href = "/login"
  }
}

export const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: handleApiError,
  }),
  mutationCache: new MutationCache({
    onError: handleApiError,
  }),
})
