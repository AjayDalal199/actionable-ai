import { MutationCache, QueryCache, QueryClient } from "@tanstack/react-query"

import { clearAccessToken } from "@/features/auth/session"
import { isInvalidSessionError } from "@/shared/lib/errors"

function redirectToLogin() {
  clearAccessToken()
  if (window.location.pathname !== "/login") {
    window.location.replace("/login")
  }
}

function handleQueryError(
  error: Error,
  query: { getObserversCount: () => number },
) {
  if (!isInvalidSessionError(error)) {
    return
  }
  clearAccessToken()
  // Route loaders fetch with no subscribers and redirect themselves.
  // A second full-page load aborts that navigation.
  if (query.getObserversCount() === 0) {
    return
  }
  if (window.location.pathname !== "/login") {
    window.location.replace("/login")
  }
}

export const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: handleQueryError,
  }),
  mutationCache: new MutationCache({
    onError: (error) => {
      if (isInvalidSessionError(error)) {
        redirectToLogin()
      }
    },
  }),
})
