import { Outlet } from "@tanstack/react-router"
import { LogOut } from "lucide-react"

import { useAuth } from "@/features/auth/useAuth"
import { AppSidebar } from "@/features/dashboard/AppSidebar"
import { Footer } from "@/shared/components/Footer"
import { Button } from "@/shared/ui/button"
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/shared/ui/sidebar"

export function DashboardLayout() {
  const { logout } = useAuth()

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <header className="bg-background sticky top-0 z-10 flex h-16 shrink-0 items-center gap-2 border-b px-4">
          <SidebarTrigger className="text-muted-foreground -ml-1" />
          <Button
            variant="ghost"
            size="sm"
            className="ml-auto"
            onClick={() => logout()}
          >
            <LogOut />
            Log out
          </Button>
        </header>
        <main className="flex-1 p-6 md:p-8">
          <div className="mx-auto max-w-7xl">
            <Outlet />
          </div>
        </main>
        <Footer />
      </SidebarInset>
    </SidebarProvider>
  )
}
