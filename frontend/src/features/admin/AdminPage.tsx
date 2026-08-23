import { useSuspenseQuery } from "@tanstack/react-query"
import { Suspense } from "react"

import type { UserPublic } from "@/api"
import { AddUser } from "@/features/admin/AddUser"
import { columns, type UserTableData } from "@/features/admin/columns"
import { PendingUsers } from "@/features/admin/PendingUsers"
import { usersQueryOptions } from "@/features/admin/queries"
import { useAuth } from "@/features/auth/useAuth"
import { DataTable } from "@/shared/components/DataTable"

function UsersTableContent() {
  const { user: currentUser } = useAuth()
  const { data: users } = useSuspenseQuery(usersQueryOptions)

  const tableData: UserTableData[] = users.data.map((user: UserPublic) => ({
    ...user,
    isCurrentUser: currentUser?.id === user.id,
  }))

  return <DataTable columns={columns} data={tableData} />
}

export function AdminPage() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Users</h1>
          <p className="text-muted-foreground">
            Manage user accounts and permissions
          </p>
        </div>
        <AddUser />
      </div>
      <Suspense fallback={<PendingUsers />}>
        <UsersTableContent />
      </Suspense>
    </div>
  )
}
