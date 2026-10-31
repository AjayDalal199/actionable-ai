import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useEffect, useState } from "react"

import { WorkspacesService } from "@/api"
import { useAuth } from "@/features/auth/useAuth"
import { canEditWorkspace } from "@/features/workspace/permissions"
import { useCurrentWorkspace } from "@/features/workspace/queries"
import { WorkspaceGate } from "@/features/workspace/WorkspaceGate"
import { useCopyToClipboard } from "@/shared/hooks/useCopyToClipboard"
import { getHttpErrorDetail } from "@/shared/lib/errors"
import { Button } from "@/shared/ui/button"

const installKey = ["workspace", "widget-install"] as const

type WidgetApi = {
  init: (options: {
    workspace: string
    token?: string | null
    apiBase?: string
  }) => void
  registerTool: (
    name: string,
    fn: (args: Record<string, unknown>) => unknown,
  ) => void
  destroy: () => void
}

declare global {
  interface Window {
    A2I?: WidgetApi
  }
}

function errorText(error: unknown, fallback: string) {
  const detail = getHttpErrorDetail(error)
  return typeof detail === "string" && detail.trim() ? detail : fallback
}

function widgetOrigin() {
  return (import.meta.env.VITE_API_URL || window.location.origin).replace(
    /\/$/,
    "",
  )
}

function snippetFor(origin: string, workspaceKey: string) {
  return `<script src="${origin}/widget.js"></script>
<script>
  A2I.init({
    workspace: "${workspaceKey}",
    token: "<end-user JWT from your backend>"
  })
  A2I.registerTool("preview_ping", function (args) {
    return { ok: true, echoed: args }
  })
</script>`
}

let widgetScript: Promise<void> | null = null

function loadWidgetScript(src: string) {
  if (window.A2I) return Promise.resolve()
  if (!widgetScript) {
    widgetScript = new Promise((resolve, reject) => {
      const script = document.createElement("script")
      script.src = src
      script.async = true
      script.onload = () => resolve()
      script.onerror = () => {
        widgetScript = null
        reject(new Error("The widget script is not built yet."))
      }
      document.head.append(script)
    })
  }
  return widgetScript
}

export function WidgetPage() {
  const { user } = useAuth()
  const { data: workspace } = useCurrentWorkspace()
  const canEdit = canEditWorkspace(user?.role)
  const isAdmin = user?.role === "admin"
  const install = useQuery({
    queryKey: installKey,
    queryFn: async () => (await WorkspacesService.readWidgetInstall()).data,
    enabled: Boolean(workspace?.id),
  })

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Widget</h1>
        <p className="text-muted-foreground">
          One script on your site. End users confirm writes in plain language.
        </p>
      </div>
      <WorkspaceGate feature="the widget">
        {install.isPending ? null : install.isError ? (
          <p className="text-sm text-destructive">
            {errorText(install.error, "Could not load the widget.")}
          </p>
        ) : install.data ? (
          <WidgetInstall
            canEdit={canEdit}
            isAdmin={isAdmin}
            secret={install.data.secret ?? null}
            workspaceKey={install.data.workspace_key}
          />
        ) : null}
      </WorkspaceGate>
    </div>
  )
}

function WidgetInstall({
  workspaceKey,
  secret,
  canEdit,
  isAdmin,
}: {
  workspaceKey: string
  secret: string | null
  canEdit: boolean
  isAdmin: boolean
}) {
  const origin = widgetOrigin()
  const snippet = snippetFor(origin, workspaceKey)
  const [copied, copy] = useCopyToClipboard()
  const [previewError, setPreviewError] = useState<string | null>(null)
  const queryClient = useQueryClient()
  const rotate = useMutation({
    mutationFn: async () =>
      (await WorkspacesService.rotateWidgetInstall()).data,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: installKey })
    },
  })

  useEffect(() => {
    let cancelled = false
    setPreviewError(null)
    void loadWidgetScript(`${origin}/widget.js`)
      .then(async () => {
        const preview = await WorkspacesService.issueWidgetPreviewToken()
        if (cancelled || !window.A2I) return
        window.A2I.registerTool("preview_ping", (args) => ({
          ok: true,
          echoed: args,
        }))
        window.A2I.init({
          workspace: workspaceKey,
          token: preview.data.token,
          apiBase: origin,
        })
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setPreviewError(
            error instanceof Error
              ? error.message
              : "The widget preview could not start.",
          )
        }
      })
    return () => {
      cancelled = true
      window.A2I?.destroy()
    }
  }, [origin, workspaceKey])

  return (
    <div className="grid max-w-3xl gap-6">
      <section className="grid gap-3">
        <h2 className="text-lg font-semibold">Snippet</h2>
        <p className="text-muted-foreground text-sm">
          Your backend signs an HS256 JWT with the workspace secret. Required
          claims are <code>sub</code> and <code>exp</code>. <code>email</code>{" "}
          is optional. The dashboard login token is not an end-user token.
        </p>
        <pre className="bg-muted overflow-auto rounded-md p-4 text-xs">
          {snippet}
        </pre>
        <div>
          <Button
            type="button"
            variant="outline"
            onClick={() => {
              void copy(snippet)
            }}
          >
            {copied === snippet ? "Copied" : "Copy snippet"}
          </Button>
        </div>
      </section>
      <section className="grid gap-2 text-sm">
        <h2 className="text-lg font-semibold">Workspace key</h2>
        <code className="bg-muted w-fit rounded px-2 py-1">{workspaceKey}</code>
        {canEdit && secret ? (
          <>
            <h2 className="mt-2 text-lg font-semibold">Signing secret</h2>
            <code className="bg-muted w-fit max-w-full overflow-auto rounded px-2 py-1">
              {secret}
            </code>
            <div>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  void copy(secret)
                }}
              >
                {copied === secret ? "Copied" : "Copy secret"}
              </Button>
            </div>
          </>
        ) : (
          <p className="text-muted-foreground">
            An editor can see the signing secret used to mint end-user tokens.
          </p>
        )}
        {isAdmin ? (
          <div>
            <Button
              type="button"
              variant="outline"
              disabled={rotate.isPending}
              onClick={() => rotate.mutate()}
            >
              Rotate secret
            </Button>
            {rotate.isError ? (
              <p className="text-destructive mt-2">
                {errorText(rotate.error, "Could not rotate the secret.")}
              </p>
            ) : null}
          </div>
        ) : null}
      </section>
      <section className="grid gap-2">
        <h2 className="text-lg font-semibold">Preview</h2>
        <p className="text-muted-foreground text-sm">
          This page mounts the real widget with a short-lived end-user token for
          your account. It also registers <code>preview_ping</code>. Internal
          chat stays on the Chat page.
        </p>
        {previewError ? (
          <p className="text-destructive text-sm">{previewError}</p>
        ) : (
          <p className="text-muted-foreground text-sm">
            Open the chat button at the bottom right.
          </p>
        )}
      </section>
    </div>
  )
}
