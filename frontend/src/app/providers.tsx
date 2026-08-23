import { QueryClientProvider } from "@tanstack/react-query"

import { queryClient } from "@/app/query-client"
import { ThemeProvider } from "@/shared/lib/theme-provider"
import { Toaster } from "@/shared/ui/sonner"

export function AppProviders({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
      <QueryClientProvider client={queryClient}>
        {children}
        <Toaster richColors closeButton />
      </QueryClientProvider>
    </ThemeProvider>
  )
}
