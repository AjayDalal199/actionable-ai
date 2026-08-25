import { EllipsisVertical } from "lucide-react"
import { useState } from "react"

import type { WorkspaceMemberPublic } from "@/api"
import { Button } from "@/shared/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/shared/ui/dropdown-menu"
import { ResendInvite } from "./ResendInvite"
import { ToggleMemberActive } from "./ToggleMemberActive"
import { UpdateMemberRole } from "./UpdateMemberRole"

export function MemberActionsMenu({
  member,
}: {
  member: WorkspaceMemberPublic
}) {
  const [open, setOpen] = useState(false)
  const joined = member.invitation_status === "accepted"

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button
          data-testid={`member-actions-${member.email}`}
          size="icon"
          variant="ghost"
        >
          <EllipsisVertical />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <UpdateMemberRole member={member} onSuccess={() => setOpen(false)} />
        {joined ? (
          <ToggleMemberActive
            member={member}
            onSuccess={() => setOpen(false)}
          />
        ) : (
          <ResendInvite member={member} onSuccess={() => setOpen(false)} />
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
