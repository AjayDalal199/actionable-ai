import { MessageSquare } from "lucide-react"

import { WorkspaceGate } from "@/features/workspace/WorkspaceGate"

export function ChatPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Chat</h1>
        <p className="text-muted-foreground">
          Internal sandbox for the same agent your customers will see
        </p>
      </div>
      <WorkspaceGate feature="Chat">
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="bg-muted mb-4 rounded-full p-4">
            <MessageSquare className="text-muted-foreground h-8 w-8" />
          </div>
          <h2 className="text-lg font-semibold">Ask a question</h2>
          <p className="text-muted-foreground mt-1 max-w-md">
            Upload a document first, then try the agent here. Internal chat uses
            your workspace knowledge and tools.
          </p>
        </div>
      </WorkspaceGate>
    </div>
  )
}
