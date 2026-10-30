import { useState } from "react"

import type { ToolPublic } from "@/api"
import { useAuth } from "@/features/auth/useAuth"
import { RegisterToolButton, ToolsBrowser } from "@/features/tools/ToolsBrowser"
import { canEditWorkspace } from "@/features/workspace/permissions"
import { useCurrentWorkspace } from "@/features/workspace/queries"
import { WorkspaceGate } from "@/features/workspace/WorkspaceGate"

export function ToolsPage() {
  const { user } = useAuth()
  const { data: workspace } = useCurrentWorkspace()
  const canEdit = canEditWorkspace(user?.role)
  const [panelOpen, setPanelOpen] = useState(false)
  const [editing, setEditing] = useState<ToolPublic | null>(null)

  const openCreate = () => {
    setEditing(null)
    setPanelOpen(true)
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Tools</h1>
          <p className="text-muted-foreground">
            Actions the agent can take, with confirmation on writes
          </p>
        </div>
        {workspace && canEdit ? (
          <RegisterToolButton
            testId="register-tool-button"
            onClick={openCreate}
          />
        ) : null}
      </div>
      <WorkspaceGate feature="Tools">
        <ToolsBrowser
          canEdit={canEdit}
          panelOpen={panelOpen}
          editing={editing}
          onCreate={openCreate}
          onEdit={(tool) => {
            setEditing(tool)
            setPanelOpen(true)
          }}
          onPanelOpenChange={(open) => {
            setPanelOpen(open)
            if (!open) {
              setEditing(null)
            }
          }}
        />
      </WorkspaceGate>
    </div>
  )
}
