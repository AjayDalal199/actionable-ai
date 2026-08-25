import { Link as RouterLink, useRouterState } from "@tanstack/react-router"
import type { LucideIcon } from "lucide-react"

import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/shared/ui/sidebar"

export type Item = {
  icon: LucideIcon
  title: string
  path:
    | "/dashboard"
    | "/dashboard/knowledge"
    | "/dashboard/tools"
    | "/dashboard/chat"
    | "/dashboard/members"
    | "/dashboard/admin"
}

interface MainProps {
  items: Item[]
}

export function Main({ items }: MainProps) {
  const { isMobile, setOpenMobile } = useSidebar()
  const router = useRouterState()
  const currentPath = router.location.pathname

  const handleMenuClick = () => {
    if (isMobile) {
      setOpenMobile(false)
    }
  }

  return (
    <SidebarGroup>
      <SidebarGroupContent>
        <SidebarMenu>
          {items.map((item) => {
            const isActive = isNavActive(currentPath, item.path)

            return (
              <SidebarMenuItem key={item.title}>
                <SidebarMenuButton
                  tooltip={item.title}
                  isActive={isActive}
                  asChild
                >
                  <RouterLink to={item.path} onClick={handleMenuClick}>
                    <item.icon />
                    <span>{item.title}</span>
                  </RouterLink>
                </SidebarMenuButton>
              </SidebarMenuItem>
            )
          })}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  )
}

function isNavActive(currentPath: string, itemPath: Item["path"]) {
  if (itemPath === "/dashboard") {
    return currentPath === "/dashboard" || currentPath === "/dashboard/"
  }
  return currentPath === itemPath || currentPath.startsWith(`${itemPath}/`)
}
