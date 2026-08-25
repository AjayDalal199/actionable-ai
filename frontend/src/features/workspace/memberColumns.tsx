import type { ColumnDef } from "@tanstack/react-table"

import type { WorkspaceMemberPublic } from "@/api"
import { cn } from "@/shared/lib/utils"
import { Badge } from "@/shared/ui/badge"
import { MemberActionsMenu } from "./MemberActionsMenu"

export type MemberTableData = WorkspaceMemberPublic & {
  isAdmin: boolean
  isCurrentUser: boolean
}

const roleLabel: Record<WorkspaceMemberPublic["role"], string> = {
  admin: "Admin",
  editor: "Editor",
  viewer: "Viewer",
}

function memberStatus(member: WorkspaceMemberPublic) {
  if (member.invitation_status === "pending") {
    return { label: "Pending", active: false }
  }
  if (member.invitation_status === "declined") {
    return { label: "Declined", active: false }
  }
  if (!member.is_active) {
    return { label: "Inactive", active: false }
  }
  return { label: "Accepted", active: true }
}

export const memberColumns: ColumnDef<MemberTableData>[] = [
  {
    accessorKey: "full_name",
    header: "Name",
    cell: ({ row }) => {
      const fullName = row.original.full_name
      return (
        <div className="flex items-center gap-2">
          <span
            className={cn("font-medium", !fullName && "text-muted-foreground")}
          >
            {fullName || "N/A"}
          </span>
          {row.original.isCurrentUser ? (
            <Badge className="text-xs" variant="outline">
              You
            </Badge>
          ) : null}
        </div>
      )
    },
  },
  {
    accessorKey: "email",
    header: "Email",
    cell: ({ row }) => (
      <span className="text-muted-foreground">{row.original.email}</span>
    ),
  },
  {
    accessorKey: "role",
    header: "Role",
    cell: ({ row }) => (
      <Badge variant="secondary" className="capitalize">
        {roleLabel[row.original.role]}
      </Badge>
    ),
  },
  {
    id: "status",
    header: "Status",
    cell: ({ row }) => {
      const status = memberStatus(row.original)
      return (
        <div
          className="flex items-center gap-2"
          data-testid={`member-status-${row.original.email}`}
        >
          <span
            className={cn(
              "size-2 rounded-full",
              status.active ? "bg-green-500" : "bg-amber-500",
              row.original.invitation_status === "declined" && "bg-gray-400",
              !row.original.is_active &&
                row.original.invitation_status === "accepted" &&
                "bg-gray-400",
            )}
          />
          <span className={status.active ? "" : "text-muted-foreground"}>
            {status.label}
          </span>
        </div>
      )
    },
  },
  {
    id: "actions",
    header: () => <span className="sr-only">Actions</span>,
    cell: ({ row }) =>
      row.original.isAdmin ? (
        <div className="flex justify-end">
          <MemberActionsMenu member={row.original} />
        </div>
      ) : null,
  },
]
