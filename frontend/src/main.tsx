import { createRouter, RouterProvider } from "@tanstack/react-router"
import { StrictMode } from "react"
import ReactDOM from "react-dom/client"
import { client } from "@/api/client.gen"
import { AppProviders } from "@/app/providers"
import { queryClient } from "@/app/query-client"
import { getAccessToken } from "@/features/auth/session"
import { routeTree } from "@/routeTree.gen"
import "@/styles/index.css"

client.setConfig({
  baseURL: import.meta.env.VITE_API_URL ?? "",
  auth: () => getAccessToken(),
})

const router = createRouter({
  routeTree,
  context: { queryClient },
})

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router
  }
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <AppProviders>
      <RouterProvider router={router} />
    </AppProviders>
  </StrictMode>,
)
