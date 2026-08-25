import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Mail } from "lucide-react"

import type { WorkspaceMemberPublic } from "@/api"
import { WorkspacesService } from "@/api"
import { workspaceKeys } from "@/features/workspace/queries"
import { useCustomToast } from "@/shared/hooks/useCustomToast"
import { handleError } from "@/shared/lib/errors"
import { DropdownMenuItem } from "@/shared/ui/dropdown-menu"

export function ResendInvite({
  member,
  onSuccess,
}: {
  member: WorkspaceMemberPublic
  onSuccess: () => void
}) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const mutation = useMutation({
    mutationFn: () =>
      WorkspacesService.inviteWorkspaceMember({
        body: {
          email: member.email,
          role: member.role,
          ...(member.full_name ? { full_name: member.full_name } : {}),
        },
      }),
    onSuccess: () => {
      showSuccessToast("Invite sent")
      onSuccess()
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: workspaceKeys.members })
    },
  })

  return (
    <DropdownMenuItem
      disabled={mutation.isPending}
      onSelect={(event) => event.preventDefault()}
      onClick={() => mutation.mutate()}
    >
      <Mail />
      Resend invite
    </DropdownMenuItem>
  )
}
