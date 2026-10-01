import type { WorkspaceMemberPublic } from "@/api"
import { useAuth } from "@/features/auth/useAuth"
import { InviteMember } from "@/features/workspace/InviteMember"
import {
  type MemberTableData,
  memberColumns,
} from "@/features/workspace/memberColumns"
import { PendingMembers } from "@/features/workspace/PendingMembers"
import {
  useCurrentWorkspace,
  useWorkspaceMembers,
} from "@/features/workspace/queries"
import { WorkspaceGate } from "@/features/workspace/WorkspaceGate"
import { DataTable } from "@/shared/components/DataTable"

function MembersTable() {
  const { user: currentUser } = useAuth()
  const { data: workspace } = useCurrentWorkspace()
  const { data: members, isPending } = useWorkspaceMembers(workspace?.id)
  const isAdmin = currentUser?.role === "admin"

  if (isPending) {
    return <PendingMembers />
  }

  const tableData: MemberTableData[] = (members?.data ?? []).map(
    (member: WorkspaceMemberPublic) => ({
      ...member,
      isAdmin,
      isCurrentUser: currentUser?.id === member.id,
    }),
  )

  return <DataTable columns={memberColumns} data={tableData} />
}

export function MembersPage() {
  const { user: currentUser } = useAuth()
  const { data: workspace } = useCurrentWorkspace()
  const isAdmin = currentUser?.role === "admin"

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Members</h1>
          <p className="text-muted-foreground">
            People who can use this workspace
          </p>
        </div>
        {isAdmin && workspace ? <InviteMember /> : null}
      </div>
      <WorkspaceGate feature="Members">
        <MembersTable />
      </WorkspaceGate>
    </div>
  )
}
