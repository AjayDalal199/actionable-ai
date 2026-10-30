import { useQuery } from "@tanstack/react-query"
import { Plus, Shield, Wrench } from "lucide-react"

import type { ToolPublic } from "@/api"
import { DeleteTool } from "@/features/tools/DeleteTool"
import { toolsQueryOptions } from "@/features/tools/queries"
import { ToolPanel } from "@/features/tools/ToolPanel"
import { useCurrentWorkspace } from "@/features/workspace/queries"
import { cn } from "@/shared/lib/utils"
import { Badge } from "@/shared/ui/badge"
import { Button } from "@/shared/ui/button"
import { Skeleton } from "@/shared/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table"
export function ToolsBrowser({
  canEdit,
  panelOpen,
  editing,
  onCreate,
  onEdit,
  onPanelOpenChange,
}: {
  canEdit: boolean
  panelOpen: boolean
  editing: ToolPublic | null
  onCreate: () => void
  onEdit: (tool: ToolPublic) => void
  onPanelOpenChange: (open: boolean) => void
}) {
  const { data: workspace } = useCurrentWorkspace()
  if (!workspace) {
    return null
  }
  return (
    <ToolsBrowserReady
      workspaceId={workspace.id}
      canEdit={canEdit}
      panelOpen={panelOpen}
      editing={editing}
      onCreate={onCreate}
      onEdit={onEdit}
      onPanelOpenChange={onPanelOpenChange}
    />
  )
}

function ToolsBrowserReady({
  workspaceId,
  canEdit,
  panelOpen,
  editing,
  onCreate,
  onEdit,
  onPanelOpenChange,
}: {
  workspaceId: string
  canEdit: boolean
  panelOpen: boolean
  editing: ToolPublic | null
  onCreate: () => void
  onEdit: (tool: ToolPublic) => void
  onPanelOpenChange: (open: boolean) => void
}) {
  const tools = useQuery(toolsQueryOptions(workspaceId))
  const columnCount = canEdit ? 4 : 3

  return (
    <>
      <Table>
        <caption className="sr-only">Tools</caption>
        <TableHeader>
          <TableRow>
            <TableHead scope="col">Name</TableHead>
            <TableHead scope="col">Type</TableHead>
            <TableHead scope="col">Safety</TableHead>
            {canEdit ? (
              <TableHead scope="col">
                <span className="sr-only">Actions</span>
              </TableHead>
            ) : null}
          </TableRow>
        </TableHeader>
        <TableBody>
          {tools.isPending ? (
            <PendingRows columns={columnCount} />
          ) : tools.isError ? (
            <TableRow className="hover:bg-transparent">
              <TableCell colSpan={columnCount} className="whitespace-normal">
                <div className="flex flex-col items-center gap-3 py-10 text-center">
                  <p className="font-medium">Couldn't load tools</p>
                  <Button
                    variant="outline"
                    onClick={() => {
                      void tools.refetch()
                    }}
                  >
                    Retry
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ) : tools.data.data.length === 0 ? (
            <TableRow className="hover:bg-transparent">
              <TableCell colSpan={columnCount} className="whitespace-normal">
                <EmptyTools canEdit={canEdit} onCreate={onCreate} />
              </TableCell>
            </TableRow>
          ) : (
            tools.data.data.map((tool) => (
              <ToolRow
                key={tool.id}
                tool={tool}
                canEdit={canEdit}
                onEdit={onEdit}
              />
            ))
          )}
        </TableBody>
      </Table>
      {canEdit ? (
        <ToolPanel
          key={panelOpen ? (editing?.id ?? "create") : "closed"}
          open={panelOpen}
          tool={editing}
          onOpenChange={onPanelOpenChange}
        />
      ) : null}
    </>
  )
}

function EmptyTools({
  canEdit,
  onCreate,
}: {
  canEdit: boolean
  onCreate: () => void
}) {
  return (
    <div className="flex flex-col items-center justify-center px-4 py-16 text-center">
      <div className="bg-muted mb-4 rounded-full p-4">
        <Wrench className="text-muted-foreground size-8" />
      </div>
      <h2 className="text-lg font-semibold">No tools registered yet</h2>
      <p className="text-muted-foreground mt-1 max-w-md">
        Point the agent at an HTTPS endpoint or a client-side function. Writes
        will ask the user to confirm first.
      </p>
      {canEdit ? (
        <div className="mt-4">
          <RegisterToolButton
            testId="register-tool-empty"
            onClick={onCreate}
            size="lg"
          />
        </div>
      ) : null}
    </div>
  )
}

function ToolRow({
  tool,
  canEdit,
  onEdit,
}: {
  tool: ToolPublic
  canEdit: boolean
  onEdit: (tool: ToolPublic) => void
}) {
  const type = tool.kind === "js" ? "JS" : (tool.http_method ?? "HTTP")
  return (
    <TableRow data-testid={`tool-row-${tool.name}`}>
      <TableCell>
        <span className="font-medium">{tool.name}</span>
      </TableCell>
      <TableCell data-testid={`tool-type-${tool.name}`}>{type}</TableCell>
      <TableCell>
        <Badge
          data-testid={`tool-safety-${tool.name}`}
          className={cn(
            "border-transparent",
            tool.requires_hitl
              ? "bg-amber-400/20 text-amber-800 dark:text-amber-200"
              : "bg-secondary text-secondary-foreground",
          )}
        >
          {tool.requires_hitl ? <Shield /> : null}
          {tool.requires_hitl ? "HITL" : "Read only"}
        </Badge>
      </TableCell>
      {canEdit ? (
        <TableCell>
          <div className="flex justify-end">
            <Button
              variant="ghost"
              size="sm"
              data-testid={`edit-tool-${tool.name}`}
              onClick={() => onEdit(tool)}
            >
              Edit
            </Button>
            <DeleteTool id={tool.id} name={tool.name} />
          </div>
        </TableCell>
      ) : null}
    </TableRow>
  )
}

function PendingRows({ columns }: { columns: number }) {
  return (
    <>
      {Array.from({ length: 4 }).map((_, index) => (
        <TableRow key={index}>
          {Array.from({ length: columns }).map((__, cell) => (
            <TableCell key={cell}>
              <Skeleton className="h-4 w-24" />
            </TableCell>
          ))}
        </TableRow>
      ))}
    </>
  )
}

export function RegisterToolButton({
  onClick,
  testId,
  size = "default",
}: {
  onClick: () => void
  testId: string
  size?: "default" | "lg"
}) {
  return (
    <Button type="button" size={size} data-testid={testId} onClick={onClick}>
      <Plus />
      Register Tool
    </Button>
  )
}
