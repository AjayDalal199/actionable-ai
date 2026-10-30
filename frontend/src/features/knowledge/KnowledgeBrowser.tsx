import { useQuery } from "@tanstack/react-query"
import { FileText } from "lucide-react"

import type { DocumentPublic, DocumentStatus } from "@/api"
import { DeleteDocument } from "@/features/knowledge/DeleteDocument"
import { documentsQueryOptions } from "@/features/knowledge/queries"
import { UploadDataButton, UploadPanel } from "@/features/knowledge/UploadPanel"
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
import { Tooltip, TooltipContent, TooltipTrigger } from "@/shared/ui/tooltip"

const statusLabel: Record<DocumentStatus, string> = {
  processing: "Processing",
  active: "Active",
  failed: "Failed",
}

const statusClass: Record<DocumentStatus, string> = {
  processing:
    "border-transparent bg-amber-400/20 text-amber-800 dark:text-amber-200",
  active:
    "border-transparent bg-emerald-500/15 text-emerald-800 dark:text-emerald-300",
  failed: "border-transparent bg-destructive/15 text-destructive",
}

export function KnowledgeBrowser({
  canEdit,
  uploadOpen,
  onUploadOpenChange,
}: {
  canEdit: boolean
  uploadOpen: boolean
  onUploadOpenChange: (open: boolean) => void
}) {
  const { data: workspace } = useCurrentWorkspace()
  if (!workspace) {
    return null
  }
  return (
    <KnowledgeBrowserReady
      workspaceId={workspace.id}
      canEdit={canEdit}
      uploadOpen={uploadOpen}
      onUploadOpenChange={onUploadOpenChange}
    />
  )
}

function KnowledgeBrowserReady({
  workspaceId,
  canEdit,
  uploadOpen,
  onUploadOpenChange,
}: {
  workspaceId: string
  canEdit: boolean
  uploadOpen: boolean
  onUploadOpenChange: (open: boolean) => void
}) {
  const documents = useQuery(documentsQueryOptions(workspaceId))
  const columnCount = canEdit ? 4 : 3

  return (
    <>
      <Table>
        <caption className="sr-only">Documents</caption>
        <TableHeader>
          <TableRow>
            <TableHead scope="col">File name</TableHead>
            <TableHead scope="col">Date</TableHead>
            <TableHead scope="col">Status</TableHead>
            {canEdit ? (
              <TableHead scope="col">
                <span className="sr-only">Actions</span>
              </TableHead>
            ) : null}
          </TableRow>
        </TableHeader>
        <TableBody>
          {documents.isPending ? (
            <PendingRows columns={columnCount} />
          ) : documents.isError ? (
            <TableRow className="hover:bg-transparent">
              <TableCell colSpan={columnCount} className="whitespace-normal">
                <div className="flex flex-col items-center gap-3 py-10 text-center">
                  <p className="font-medium">Couldn't load documents</p>
                  <Button
                    variant="outline"
                    onClick={() => {
                      void documents.refetch()
                    }}
                  >
                    Retry
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ) : documents.data.data.length === 0 ? (
            <TableRow className="hover:bg-transparent">
              <TableCell colSpan={columnCount} className="whitespace-normal">
                <EmptyDocuments
                  canEdit={canEdit}
                  onUpload={() => onUploadOpenChange(true)}
                />
              </TableCell>
            </TableRow>
          ) : (
            documents.data.data.map((document) => (
              <DocumentRow
                key={document.id}
                document={document}
                canEdit={canEdit}
              />
            ))
          )}
        </TableBody>
      </Table>
      {canEdit ? (
        <UploadPanel open={uploadOpen} onOpenChange={onUploadOpenChange} />
      ) : null}
    </>
  )
}

function EmptyDocuments({
  canEdit,
  onUpload,
}: {
  canEdit: boolean
  onUpload: () => void
}) {
  return (
    <div className="flex flex-col items-center justify-center px-4 py-16 text-center">
      <div className="bg-muted mb-4 rounded-full p-4">
        <FileText className="text-muted-foreground size-8" />
      </div>
      <p className="max-w-md text-lg font-semibold">
        Your AI has no knowledge yet. Upload your first document to get started.
      </p>
      {canEdit ? (
        <div className="mt-4">
          <UploadDataButton
            size="lg"
            testId="upload-data-empty"
            onClick={onUpload}
          />
        </div>
      ) : null}
    </div>
  )
}

function DocumentRow({
  document,
  canEdit,
}: {
  document: DocumentPublic
  canEdit: boolean
}) {
  const filename = document.original_filename || document.title
  return (
    <TableRow data-testid={`document-row-${document.id}`}>
      <TableCell>
        <span className="block max-w-xs truncate font-medium" title={filename}>
          {filename}
        </span>
      </TableCell>
      <TableCell className="text-muted-foreground">
        {formatDocumentDate(document.created_at ?? null)}
      </TableCell>
      <TableCell className="whitespace-normal">
        <DocumentStatusBadge document={document} />
      </TableCell>
      {canEdit ? (
        <TableCell>
          <div className="flex justify-end">
            <DeleteDocument id={document.id} filename={filename} />
          </div>
        </TableCell>
      ) : null}
    </TableRow>
  )
}

function DocumentStatusBadge({ document }: { document: DocumentPublic }) {
  const badge = (
    <Badge
      className={cn(statusClass[document.status])}
      data-testid={`document-status-${document.id}`}
    >
      <span className="sr-only">Status: </span>
      {statusLabel[document.status]}
    </Badge>
  )
  return (
    <div className="flex max-w-xs flex-col items-start gap-1">
      {document.status === "failed" && document.error_message ? (
        <Tooltip>
          <TooltipTrigger asChild>{badge}</TooltipTrigger>
          <TooltipContent className="max-w-xs">
            {document.error_message}
          </TooltipContent>
        </Tooltip>
      ) : (
        badge
      )}
      {document.status === "failed" && document.error_message ? (
        <p
          className="text-destructive text-xs whitespace-normal"
          data-testid={`document-error-${document.id}`}
        >
          {document.error_message}
        </p>
      ) : null}
    </div>
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

function formatDocumentDate(value: string | null): string {
  if (!value) {
    return "—"
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return "—"
  }
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(date)
}
