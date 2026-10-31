import { useState } from "react"

import { useAuth } from "@/features/auth/useAuth"
import { KnowledgeBrowser } from "@/features/knowledge/KnowledgeBrowser"
import { UploadDataButton } from "@/features/knowledge/UploadPanel"
import { canEditWorkspace } from "@/features/workspace/permissions"
import { useCurrentWorkspace } from "@/features/workspace/queries"
import { WorkspaceGate } from "@/features/workspace/WorkspaceGate"

export function KnowledgePage() {
  const { user } = useAuth()
  const { data: workspace } = useCurrentWorkspace()
  const canEdit = canEditWorkspace(user?.role)
  const [uploadOpen, setUploadOpen] = useState(false)

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Knowledge</h1>
          <p className="text-muted-foreground">
            Documents the agent can answer from
          </p>
        </div>
        {workspace && canEdit ? (
          <UploadDataButton
            testId="upload-data-button"
            onClick={() => setUploadOpen(true)}
          />
        ) : null}
      </div>
      <WorkspaceGate feature="Knowledge">
        <KnowledgeBrowser
          canEdit={canEdit}
          uploadOpen={uploadOpen}
          onUploadOpenChange={setUploadOpen}
        />
      </WorkspaceGate>
    </div>
  )
}
