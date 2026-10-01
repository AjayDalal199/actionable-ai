import { Wrench } from "lucide-react"

import { WorkspaceGate } from "@/features/workspace/WorkspaceGate"

export function ToolsPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Tools</h1>
        <p className="text-muted-foreground">
          Actions the agent can take, with confirmation on writes
        </p>
      </div>
      <WorkspaceGate feature="Tools">
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="bg-muted mb-4 rounded-full p-4">
            <Wrench className="text-muted-foreground h-8 w-8" />
          </div>
          <h2 className="text-lg font-semibold">No tools registered yet</h2>
          <p className="text-muted-foreground mt-1 max-w-md">
            Point the agent at an HTTPS endpoint or a client-side function.
            Writes will ask the user to confirm first.
          </p>
        </div>
      </WorkspaceGate>
    </div>
  )
}
