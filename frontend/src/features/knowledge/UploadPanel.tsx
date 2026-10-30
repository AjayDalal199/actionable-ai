import { useQueryClient } from "@tanstack/react-query"
import axios from "axios"
import { Upload } from "lucide-react"
import { useEffect, useRef, useState } from "react"
import { toast } from "sonner"

import { KnowledgeService } from "@/api"
import {
  fileRejection,
  UPLOAD_INTERRUPTED_MESSAGE,
} from "@/features/knowledge/files"
import { documentKeys } from "@/features/knowledge/queries"
import { getHttpErrorDetail } from "@/shared/lib/errors"
import { cn } from "@/shared/lib/utils"
import { Button } from "@/shared/ui/button"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/shared/ui/sheet"

type UploadStatus = "queued" | "uploading" | "done" | "error"

type UploadItem = {
  id: string
  name: string
  progress: number
  status: UploadStatus
  message?: string
}

type Rejection = {
  id: string
  name: string
  message: string
}

type QueuedFile = {
  id: string
  file: File
}

export function UploadPanel({
  open,
  onOpenChange,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const queryClient = useQueryClient()
  const inputRef = useRef<HTMLInputElement>(null)
  const queueRef = useRef<QueuedFile[]>([])
  const pumpingRef = useRef(false)
  const wasOpenRef = useRef(false)
  const [dragDepth, setDragDepth] = useState(0)
  const [items, setItems] = useState<UploadItem[]>([])
  const [rejections, setRejections] = useState<Rejection[]>([])

  useEffect(() => {
    if (open && !wasOpenRef.current) {
      setRejections([])
      setItems((current) =>
        current.filter(
          (item) => item.status === "queued" || item.status === "uploading",
        ),
      )
    }
    wasOpenRef.current = open
  }, [open])

  const acceptFiles = (list: FileList | File[]) => {
    const incoming = Array.from(list)
    if (incoming.length === 0) {
      return
    }
    const nextRejections: Rejection[] = []
    const queued: QueuedFile[] = []
    for (const file of incoming) {
      const message = fileRejection(file)
      if (message) {
        nextRejections.push({
          id: crypto.randomUUID(),
          name: file.name,
          message,
        })
        continue
      }
      const id = crypto.randomUUID()
      queued.push({ id, file })
    }
    if (nextRejections.length > 0) {
      setRejections((current) => [...nextRejections, ...current])
    }
    if (queued.length === 0) {
      return
    }
    setItems((current) => [
      ...queued.map((entry) => ({
        id: entry.id,
        name: entry.file.name,
        progress: 0,
        status: "queued" as const,
      })),
      ...current,
    ])
    queueRef.current.push(...queued)
    void pump()
  }

  const pump = async () => {
    if (pumpingRef.current) {
      return
    }
    pumpingRef.current = true
    try {
      while (queueRef.current.length > 0) {
        const next = queueRef.current.shift()
        if (!next) {
          break
        }
        const outcome = await uploadOne(next)
        if (outcome === "interrupted") {
          const skipped = queueRef.current.splice(0)
          setItems((current) =>
            current.map((item) =>
              skipped.some((entry) => entry.id === item.id)
                ? {
                    ...item,
                    status: "error",
                    message: UPLOAD_INTERRUPTED_MESSAGE,
                  }
                : item,
            ),
          )
          break
        }
      }
    } finally {
      pumpingRef.current = false
      if (queueRef.current.length > 0) {
        void pump()
      }
    }
  }

  const uploadOne = async (
    entry: QueuedFile,
  ): Promise<"ok" | "failed" | "interrupted"> => {
    setItems((current) =>
      current.map((item) =>
        item.id === entry.id
          ? { ...item, status: "uploading", progress: 0 }
          : item,
      ),
    )
    try {
      await KnowledgeService.uploadKnowledge({
        body: { file: entry.file },
        onUploadProgress: (event) => {
          const total =
            event.total && event.total > 0 ? event.total : entry.file.size
          const progress =
            total > 0
              ? Math.min(100, Math.round((event.loaded / total) * 100))
              : 0
          setItems((current) =>
            current.map((item) =>
              item.id === entry.id ? { ...item, progress } : item,
            ),
          )
        },
      })
      setItems((current) =>
        current.map((item) =>
          item.id === entry.id
            ? { ...item, status: "done", progress: 100 }
            : item,
        ),
      )
      await queryClient.invalidateQueries({ queryKey: documentKeys.all })
      return "ok"
    } catch (error) {
      if (isUploadInterrupted(error)) {
        toast.error(UPLOAD_INTERRUPTED_MESSAGE)
        setItems((current) =>
          current.map((item) =>
            item.id === entry.id
              ? {
                  ...item,
                  status: "error",
                  message: UPLOAD_INTERRUPTED_MESSAGE,
                }
              : item,
          ),
        )
        return "interrupted"
      }
      setItems((current) =>
        current.map((item) =>
          item.id === entry.id
            ? {
                ...item,
                status: "error",
                message: uploadFailureMessage(error),
              }
            : item,
        ),
      )
      return "failed"
    }
  }

  const dragging = dragDepth > 0

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full overflow-y-auto sm:max-w-md">
        <SheetHeader>
          <SheetTitle>Upload Data</SheetTitle>
          <SheetDescription>
            PDF, Markdown, or text. Up to 10MB each. You can add several files
            at once.
          </SheetDescription>
        </SheetHeader>
        <div className="flex flex-col gap-4 px-4 pb-6">
          <button
            type="button"
            data-testid="knowledge-dropzone"
            className={cn(
              "border-border bg-muted/40 flex min-h-40 w-full flex-col items-center justify-center rounded-lg border-2 border-dashed px-6 py-8 text-center transition-colors",
              dragging && "border-primary bg-primary/10 border-solid",
            )}
            onClick={() => inputRef.current?.click()}
            onDragEnter={(event) => {
              event.preventDefault()
              setDragDepth((depth) => depth + 1)
            }}
            onDragOver={(event) => {
              event.preventDefault()
            }}
            onDragLeave={(event) => {
              event.preventDefault()
              setDragDepth((depth) => Math.max(0, depth - 1))
            }}
            onDrop={(event) => {
              event.preventDefault()
              setDragDepth(0)
              acceptFiles(event.dataTransfer.files)
            }}
          >
            <Upload className="text-muted-foreground mb-3 size-6" />
            <span className="text-sm font-medium">
              {dragging
                ? "Drop to upload."
                : "Drag and drop files here, or click to browse."}
            </span>
          </button>
          <input
            ref={inputRef}
            type="file"
            className="sr-only"
            tabIndex={-1}
            multiple
            accept=".pdf,.md,.markdown,.txt,application/pdf,text/plain,text/markdown"
            aria-hidden
            data-testid="knowledge-file-input"
            onChange={(event) => {
              if (event.target.files) {
                acceptFiles(event.target.files)
              }
              event.target.value = ""
            }}
          />
          {rejections.length > 0 ? (
            <ul className="flex flex-col gap-2" role="alert">
              {rejections.map((rejection) => (
                <li
                  key={rejection.id}
                  className="border-destructive/40 bg-destructive/10 rounded-md border px-3 py-2 text-sm"
                >
                  <p className="font-medium">{rejection.name}</p>
                  <p className="text-destructive mt-1">{rejection.message}</p>
                </li>
              ))}
            </ul>
          ) : null}
          {items.length > 0 ? (
            <ul className="flex flex-col gap-3" aria-live="polite">
              {items.map((item) => (
                <li key={item.id} className="flex flex-col gap-1.5">
                  <div className="flex items-center justify-between gap-3 text-sm">
                    <span className="truncate font-medium">{item.name}</span>
                    <span className="text-muted-foreground shrink-0">
                      {item.status === "queued"
                        ? "Waiting"
                        : item.status === "uploading"
                          ? `${item.progress}%`
                          : item.status === "done"
                            ? "Uploaded"
                            : "Failed"}
                    </span>
                  </div>
                  {item.status === "uploading" || item.status === "done" ? (
                    <div
                      role="progressbar"
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-valuenow={item.progress}
                      aria-label={`Upload progress for ${item.name}`}
                      className="bg-muted h-2 overflow-hidden rounded-full"
                    >
                      <div
                        className="bg-primary h-full transition-[width]"
                        style={{ width: `${item.progress}%` }}
                      />
                    </div>
                  ) : null}
                  {item.message ? (
                    <p className="text-destructive text-sm">{item.message}</p>
                  ) : null}
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      </SheetContent>
    </Sheet>
  )
}

export function UploadDataButton({
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
      <Upload />
      Upload Data
    </Button>
  )
}

function isUploadInterrupted(error: unknown): boolean {
  return axios.isAxiosError(error) && !error.response
}

function uploadFailureMessage(error: unknown): string {
  const detail = getHttpErrorDetail(error)
  if (typeof detail === "string" && detail) {
    return detail
  }
  return "Upload failed."
}
