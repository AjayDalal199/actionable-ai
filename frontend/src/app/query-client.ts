import { MutationCache, QueryCache, QueryClient } from "@tanstack/react-query"

import { clearAccessToken } from "@/features/auth/session"
import { getHttpErrorDetail, getHttpErrorStatus } from "@/shared/lib/errors"

function isCredentialAuthError(error: unknown): boolean {
  const status = getHttpErrorStatus(error)
  if (status === 401) {
    return true
  }
  return (
    status === 403 &&
    getHttpErrorDetail(error) === "Could not validate credentials"
  )
}

function handleApiError(error: Error) {
  if (isCredentialAuthError(error)) {
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
