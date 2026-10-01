import { useMutation, useQueryClient } from "@tanstack/react-query"
import { UserMinus, UserPlus } from "lucide-react"
import { useState } from "react"

import type { WorkspaceMemberPublic } from "@/api"
import { WorkspacesService } from "@/api"
import { invalidateWorkspaceSession } from "@/features/workspace/queries"
import { useCustomToast } from "@/shared/hooks/useCustomToast"
import { handleError } from "@/shared/lib/errors"
import { Button } from "@/shared/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog"
import { DropdownMenuItem } from "@/shared/ui/dropdown-menu"
import { LoadingButton } from "@/shared/ui/loading-button"

export function ToggleMemberActive({
  member,
  onSuccess,
}: {
  member: WorkspaceMemberPublic
  onSuccess: () => void
}) {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const nextActive = !member.is_active

  const mutation = useMutation({
    mutationFn: () =>
      WorkspacesService.updateWorkspaceMember({
        path: { user_id: member.id },
        body: { is_active: nextActive },
      }),
    onSuccess: () => {
      showSuccessToast(nextActive ? "Member reactivated" : "Member deactivated")
      setIsOpen(false)
      onSuccess()
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      void invalidateWorkspaceSession(queryClient)
    },
  })

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuItem
        variant={nextActive ? "default" : "destructive"}
        onSelect={(event) => event.preventDefault()}
        onClick={() => setIsOpen(true)}
      >
        {nextActive ? <UserPlus /> : <UserMinus />}
        {nextActive ? "Reactivate" : "Deactivate"}
      </DropdownMenuItem>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>
            {nextActive ? "Reactivate member" : "Deactivate member"}
          </DialogTitle>
          <DialogDescription>
            {nextActive
              ? `${member.email} will be able to use this workspace again.`
              : `${member.email} will lose access to this workspace until you invite or reactivate them.`}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter className="mt-4">
          <DialogClose asChild>
            <Button variant="outline" disabled={mutation.isPending}>
              Cancel
            </Button>
          </DialogClose>
          <LoadingButton
            loading={mutation.isPending}
            onClick={() => mutation.mutate()}
            variant={nextActive ? "default" : "destructive"}
          >
            {nextActive ? "Reactivate" : "Deactivate"}
          </LoadingButton>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
