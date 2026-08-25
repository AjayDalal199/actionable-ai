import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Building2, ChevronsUpDown, Plus } from "lucide-react"
import { useState } from "react"

import { WorkspacesService } from "@/api"
import { CreateWorkspaceForm } from "@/features/workspace/CreateWorkspaceForm"
import {
  invalidateWorkspaceSession,
  useWorkspaces,
  workspaceKeys,
} from "@/features/workspace/queries"
import { useCustomToast } from "@/shared/hooks/useCustomToast"
import { handleError } from "@/shared/lib/errors"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/shared/ui/dropdown-menu"
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/shared/ui/sidebar"
import { Skeleton } from "@/shared/ui/skeleton"

export function WorkspaceSwitcher() {
  const queryClient = useQueryClient()
  const { isMobile, setOpenMobile } = useSidebar()
  const { data, isPending } = useWorkspaces()
  const { showErrorToast, showSuccessToast } = useCustomToast()
  const [createOpen, setCreateOpen] = useState(false)

  const current = data?.data.find((workspace) => workspace.is_current)
  const label = current?.name ?? "No workspace"

  const switchMutation = useMutation({
    mutationFn: (workspace_id: string) =>
      WorkspacesService.selectCurrentWorkspace({ body: { workspace_id } }),
    onSuccess: (response) => {
      queryClient.setQueryData(workspaceKeys.current, response.data)
      showSuccessToast(`Switched to ${response.data.name}`)
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => invalidateWorkspaceSession(queryClient),
  })

  if (isPending) {
    return <Skeleton className="h-12 w-full" />
  }

  return (
    <>
      <SidebarMenu>
        <SidebarMenuItem>
          <DropdownMenu modal={false}>
            <DropdownMenuTrigger asChild>
              <SidebarMenuButton
                size="lg"
                className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
                data-testid="workspace-switcher"
              >
                <div className="bg-sidebar-accent flex size-8 items-center justify-center rounded-md">
                  <Building2 className="size-4" />
                </div>
                <div className="grid flex-1 text-left text-sm leading-tight">
                  <span className="truncate font-medium">{label}</span>
                  <span className="text-muted-foreground truncate text-xs capitalize">
                    {current?.role ?? "Select a workspace"}
                  </span>
                </div>
                <ChevronsUpDown className="ml-auto size-4 text-muted-foreground" />
              </SidebarMenuButton>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              className="w-(--radix-dropdown-menu-trigger-width) min-w-56 rounded-lg"
              side={isMobile ? "bottom" : "right"}
              align="end"
              sideOffset={4}
            >
              <DropdownMenuLabel>Workspaces</DropdownMenuLabel>
              {data?.data.length ? (
                <DropdownMenuRadioGroup
                  value={current?.id ?? ""}
                  onValueChange={(workspaceId) => {
                    if (workspaceId && workspaceId !== current?.id) {
                      switchMutation.mutate(workspaceId)
                    }
                    if (isMobile) {
                      setOpenMobile(false)
                    }
                  }}
                >
                  {data.data.map((workspace) => (
                    <DropdownMenuRadioItem
                      key={workspace.id}
                      value={workspace.id}
                    >
                      {workspace.name}
                    </DropdownMenuRadioItem>
                  ))}
                </DropdownMenuRadioGroup>
              ) : (
                <p className="text-muted-foreground px-2 py-1.5 text-sm">
                  You have not joined a workspace yet.
                </p>
              )}
              {data?.can_create ? (
                <>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    data-testid="workspace-switcher-create"
                    onSelect={() => setCreateOpen(true)}
                  >
                    <Plus />
                    Create workspace
                  </DropdownMenuItem>
                </>
              ) : null}
            </DropdownMenuContent>
          </DropdownMenu>
        </SidebarMenuItem>
      </SidebarMenu>
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create a workspace</DialogTitle>
            <DialogDescription>
              You can create one workspace. Join others by invite.
            </DialogDescription>
          </DialogHeader>
          <CreateWorkspaceForm onCreated={() => setCreateOpen(false)} />
        </DialogContent>
      </Dialog>
    </>
  )
}
