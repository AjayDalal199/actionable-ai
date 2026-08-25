import { BookOpen, Home, MessageSquare, Users, Wrench } from "lucide-react"

import { useAuth } from "@/features/auth/useAuth"
import { WorkspaceSwitcher } from "@/features/workspace/WorkspaceSwitcher"
import { SidebarAppearance } from "@/shared/components/Appearance"
import { Logo } from "@/shared/components/Logo"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
} from "@/shared/ui/sidebar"
import { type Item, Main } from "./Main"
import { User } from "./User"

const baseItems: Item[] = [
  { icon: Home, title: "Dashboard", path: "/dashboard" },
  { icon: BookOpen, title: "Knowledge", path: "/dashboard/knowledge" },
  { icon: Wrench, title: "Tools", path: "/dashboard/tools" },
  { icon: MessageSquare, title: "Chat", path: "/dashboard/chat" },
]

export function AppSidebar() {
  const { user: currentUser } = useAuth()

  const items: Item[] = currentUser?.is_superuser
    ? [...baseItems, { icon: Users, title: "Admin", path: "/dashboard/admin" }]
    : baseItems

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="px-4 py-6 group-data-[collapsible=icon]:px-0 group-data-[collapsible=icon]:items-center">
        <Logo variant="responsive" />
      </SidebarHeader>
      <SidebarContent>
        <Main items={items} />
      </SidebarContent>
      <SidebarFooter>
        <WorkspaceSwitcher />
        <SidebarAppearance />
        <User user={currentUser} />
      </SidebarFooter>
    </Sidebar>
  )
}
