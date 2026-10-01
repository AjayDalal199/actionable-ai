import { MutationCache, QueryCache, QueryClient } from "@tanstack/react-query"

import { clearAccessToken } from "@/features/auth/session"
import { isInvalidSessionError } from "@/shared/lib/errors"

function handleApiError(error: Error) {
  if (isInvalidSessionError(error)) {
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
