import type { QueryClient } from "@tanstack/react-query"
import { ReactQueryDevtools } from "@tanstack/react-query-devtools"
import {
  createRootRouteWithContext,
  HeadContent,
  Outlet,
  useRouterState,
} from "@tanstack/react-router"
import { TanStackRouterDevtools } from "@tanstack/react-router-devtools"

import { ErrorComponent } from "@/shared/components/ErrorComponent"
import { NotFound } from "@/shared/components/NotFound"

export const Route = createRootRouteWithContext<{
  queryClient: QueryClient
}>()({
  component: RootComponent,
  notFoundComponent: () => <NotFound />,
  errorComponent: () => <ErrorComponent />,
})

function RootComponent() {
  const pathname = useRouterState({ select: (s) => s.location.pathname })
  const showDevtools = import.meta.env.DEV && pathname.startsWith("/dashboard")

  return (
    <>
      <HeadContent />
      <Outlet />
      {showDevtools ? (
        <>
          <TanStackRouterDevtools position="bottom-right" />
          <ReactQueryDevtools initialIsOpen={false} />
        </>
      ) : null}
    </>
  )
}
