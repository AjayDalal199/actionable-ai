import { FileText } from "lucide-react"

import { WorkspaceGate } from "@/features/workspace/WorkspaceGate"

export function KnowledgePage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Knowledge</h1>
        <p className="text-muted-foreground">
          Documents the agent can answer from
        </p>
      </div>
      <WorkspaceGate feature="Knowledge">
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="bg-muted mb-4 rounded-full p-4">
            <FileText className="text-muted-foreground h-8 w-8" />
          </div>
          <h2 className="text-lg font-semibold">
            Your AI has no knowledge yet
          </h2>
          <p className="text-muted-foreground mt-1 max-w-md">
            Upload your first document to get started. PDFs and Markdown will
            land here.
          </p>
        </div>
      </WorkspaceGate>
    </div>
  )
}
