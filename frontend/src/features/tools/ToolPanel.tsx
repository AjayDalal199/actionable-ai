import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import {
  type HttpMethod,
  type ToolPublic,
  type ToolRegister,
  ToolsService,
  type ToolUpdate,
} from "@/api"
import { toolKeys } from "@/features/tools/queries"
import {
  DEFAULT_SCHEMA_TEXT,
  isWriteMethod,
  parseToolSchema,
  TOOL_NAME_MESSAGE,
  toolNameError,
  toolUrlError,
  WRITE_HITL_REASON,
} from "@/features/tools/schema"
import { useCustomToast } from "@/shared/hooks/useCustomToast"
import {
  getHttpErrorDetail,
  getHttpErrorStatus,
  handleError,
} from "@/shared/lib/errors"
import { cn } from "@/shared/lib/utils"
import { Button } from "@/shared/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog"
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/shared/ui/form"
import { Input } from "@/shared/ui/input"
import { Label } from "@/shared/ui/label"
import { LoadingButton } from "@/shared/ui/loading-button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/ui/select"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/shared/ui/sheet"
import { Textarea } from "@/shared/ui/textarea"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/shared/ui/tooltip"

const formSchema = z
  .object({
    name: z.string(),
    kind: z.enum(["http", "js"]),
    url: z.string(),
    http_method: z.enum(["GET", "POST", "PUT", "DELETE"]),
    description: z.string(),
    schemaText: z.string(),
    requires_hitl: z.boolean(),
  })
  .superRefine((value, ctx) => {
    if (toolNameError(value.name)) {
      ctx.addIssue({
        code: "custom",
        message: TOOL_NAME_MESSAGE,
        path: ["name"],
      })
    }
    const parsed = parseToolSchema(value.schemaText)
    if (!parsed.ok) {
      ctx.addIssue({
        code: "custom",
        message: parsed.message,
        path: ["schemaText"],
      })
    }
    const urlMessage = value.kind === "http" ? toolUrlError(value.url) : null
    if (urlMessage) {
      ctx.addIssue({
        code: "custom",
        message: urlMessage,
        path: ["url"],
      })
    }
  })

type FormValues = z.infer<typeof formSchema>

const emptyValues: FormValues = {
  name: "",
  kind: "http",
  url: "",
  http_method: "GET",
  description: "",
  schemaText: DEFAULT_SCHEMA_TEXT,
  requires_hitl: false,
}

function valuesFrom(tool: ToolPublic | null): FormValues {
  if (!tool) {
    return emptyValues
  }
  return {
    name: tool.name,
    kind: tool.kind,
    url: tool.url ?? "",
    http_method: tool.http_method ?? "GET",
    description: tool.description,
    schemaText: JSON.stringify(tool.schema, null, 2),
    requires_hitl: tool.requires_hitl,
  }
}

export function ToolPanel({
  open,
  tool,
  onOpenChange,
}: {
  open: boolean
  tool: ToolPublic | null
  onOpenChange: (open: boolean) => void
}) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [confirmOpen, setConfirmOpen] = useState(false)
  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    mode: "onChange",
    defaultValues: valuesFrom(tool),
  })
  const isEditing = tool !== null

  const watched = form.watch()
  const hitlLocked =
    watched.kind === "http" && isWriteMethod(watched.http_method)
  const canSave =
    toolNameError(watched.name) === null &&
    parseToolSchema(watched.schemaText).ok &&
    (watched.kind === "js" || toolUrlError(watched.url) === null)
  const isDirty = form.formState.isDirty

  const requestClose = () => {
    if (isDirty) {
      setConfirmOpen(true)
      return
    }
    onOpenChange(false)
  }

  const discard = () => {
    form.reset(valuesFrom(tool))
    setConfirmOpen(false)
    onOpenChange(false)
  }

  const mutation = useMutation({
    mutationFn: async (values: FormValues) => {
      const parsed = parseToolSchema(values.schemaText)
      if (!parsed.ok) {
        throw new Error(parsed.message)
      }
      const requiresHitl =
        values.kind === "http" && isWriteMethod(values.http_method)
          ? true
          : values.requires_hitl
      if (tool) {
        const body: ToolUpdate =
          values.kind === "js"
            ? {
                description: values.description,
                schema: parsed.value,
                requires_hitl: requiresHitl,
              }
            : {
                description: values.description,
                schema: parsed.value,
                requires_hitl: requiresHitl,
                http_method: values.http_method,
                url: values.url.trim(),
              }
        await ToolsService.updateTool({
          path: { tool_id: tool.id },
          body,
        })
        return
      }
      const body: ToolRegister =
        values.kind === "js"
          ? {
              name: values.name,
              kind: "js",
              description: values.description,
              schema: parsed.value,
              requires_hitl: requiresHitl,
            }
          : {
              name: values.name,
              kind: "http",
              http_method: values.http_method as HttpMethod,
              url: values.url.trim(),
              description: values.description,
              schema: parsed.value,
              requires_hitl: requiresHitl,
            }
      await ToolsService.registerTool({ body })
    },
    onSuccess: (_data, values) => {
      showSuccessToast(tool ? "Tool updated" : "Tool registered")
      form.reset(values)
      onOpenChange(false)
    },
    onError: (error) => {
      if (!tool && getHttpErrorStatus(error) === 409) {
        const detail = getHttpErrorDetail(error)
        form.setError("name", {
          message:
            typeof detail === "string"
              ? detail
              : "A tool with this name already exists.",
        })
        form.setFocus("name")
        return
      }
      handleError.call(showErrorToast, error as Error)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: toolKeys.all })
    },
  })

  return (
    <>
      <Sheet
        open={open}
        onOpenChange={(next) => {
          if (next) {
            onOpenChange(true)
            return
          }
          requestClose()
        }}
      >
        <SheetContent
          className="w-full gap-0 overflow-hidden p-0 sm:max-w-xl"
          onEscapeKeyDown={(event) => {
            const target = event.target
            if (
              target instanceof HTMLElement &&
              target.dataset.testid === "tool-schema"
            ) {
              event.preventDefault()
              document.getElementById("tool-save")?.focus()
            }
          }}
        >
          <SheetHeader className="border-b">
            <SheetTitle>{isEditing ? "Edit tool" : "Register tool"}</SheetTitle>
            <SheetDescription>
              {watched.kind === "js"
                ? "JavaScript tools are stored here. They are not executed in this dashboard."
                : "HTTP tools run on your server. Writes always ask the user to confirm."}
            </SheetDescription>
          </SheetHeader>
          <Form {...form}>
            <form
              className="flex min-h-0 flex-1 flex-col"
              onSubmit={form.handleSubmit((values) => {
                if (!canSave) {
                  return
                }
                mutation.mutate(values)
              })}
            >
              <div className="flex flex-1 flex-col gap-4 overflow-y-auto px-4 py-4">
                <FormField
                  control={form.control}
                  name="kind"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Type</FormLabel>
                      <Select
                        value={field.value}
                        disabled={isEditing}
                        onValueChange={(value) => {
                          field.onChange(value)
                          if (value === "js") {
                            form.setValue("url", "")
                            form.setValue("http_method", "GET")
                            form.clearErrors("url")
                          }
                        }}
                      >
                        <FormControl>
                          <SelectTrigger
                            className="w-full"
                            data-testid="tool-kind"
                          >
                            <SelectValue />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="http">HTTP</SelectItem>
                          <SelectItem value="js">JavaScript</SelectItem>
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>
                        Name <span className="text-destructive">*</span>
                      </FormLabel>
                      <FormControl>
                        <Input
                          {...field}
                          data-testid="tool-name"
                          autoComplete="off"
                          readOnly={isEditing}
                          className={isEditing ? "bg-muted" : undefined}
                          placeholder="cancel_subscription"
                        />
                      </FormControl>
                      <FormDescription>
                        {isEditing
                          ? "Names can't be changed."
                          : "Lowercase letters, numbers, and underscores."}
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                {watched.kind === "http" ? (
                  <>
                    <FormField
                      control={form.control}
                      name="url"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>
                            URL <span className="text-destructive">*</span>
                          </FormLabel>
                          <FormControl>
                            <Input
                              {...field}
                              data-testid="tool-url"
                              autoComplete="off"
                              placeholder="https://api.example.com/v1/resource"
                              spellCheck={false}
                            />
                          </FormControl>
                          <FormDescription>
                            HTTPS, or HTTP for localhost, 127.0.0.1, and ::1.
                          </FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={form.control}
                      name="http_method"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Method</FormLabel>
                          <Select
                            value={field.value}
                            onValueChange={(value) => {
                              field.onChange(value)
                              if (isWriteMethod(value)) {
                                form.setValue("requires_hitl", true, {
                                  shouldDirty: true,
                                })
                              }
                            }}
                          >
                            <FormControl>
                              <SelectTrigger
                                className="w-full"
                                data-testid="tool-method"
                              >
                                <SelectValue />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              <SelectItem value="GET">GET</SelectItem>
                              <SelectItem value="POST">POST</SelectItem>
                              <SelectItem value="PUT">PUT</SelectItem>
                              <SelectItem value="DELETE">DELETE</SelectItem>
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </>
                ) : null}
                <FormField
                  control={form.control}
                  name="description"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Description</FormLabel>
                      <FormControl>
                        <Textarea
                          {...field}
                          rows={3}
                          data-testid="tool-description"
                          placeholder="What this tool does"
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="requires_hitl"
                  render={({ field }) => {
                    const checked = hitlLocked || field.value
                    const switchControl = (
                      <HitlSwitch
                        checked={checked}
                        disabled={hitlLocked}
                        describedBy={
                          hitlLocked ? "tool-hitl-reason" : undefined
                        }
                        onCheckedChange={(next) => {
                          if (!hitlLocked) {
                            field.onChange(next)
                          }
                        }}
                      />
                    )
                    return (
                      <FormItem>
                        <div className="flex items-center justify-between gap-4">
                          <Label htmlFor="tool-hitl">
                            Requires Human-in-the-Loop Confirmation
                          </Label>
                          {hitlLocked ? (
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <span className="inline-flex">
                                  {switchControl}
                                </span>
                              </TooltipTrigger>
                              <TooltipContent className="max-w-xs">
                                {WRITE_HITL_REASON}
                              </TooltipContent>
                            </Tooltip>
                          ) : (
                            switchControl
                          )}
                        </div>
                        {hitlLocked ? (
                          <p
                            id="tool-hitl-reason"
                            className="text-muted-foreground text-sm"
                            data-testid="tool-hitl-reason"
                          >
                            {WRITE_HITL_REASON}
                          </p>
                        ) : (
                          <p className="text-muted-foreground text-sm">
                            Turn this on to ask the user before the tool runs.
                          </p>
                        )}
                        <FormMessage />
                      </FormItem>
                    )
                  }}
                />
                <FormField
                  control={form.control}
                  name="schemaText"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>
                        JSON schema <span className="text-destructive">*</span>
                      </FormLabel>
                      <FormControl>
                        <Textarea
                          {...field}
                          rows={12}
                          spellCheck={false}
                          data-testid="tool-schema"
                          className="field-sizing-fixed min-h-48 font-mono text-sm"
                          aria-label="JSON schema"
                          onKeyDown={(event) => {
                            if (event.key !== "Escape") {
                              return
                            }
                            event.preventDefault()
                            event.stopPropagation()
                            document.getElementById("tool-save")?.focus()
                          }}
                        />
                      </FormControl>
                      <FormDescription>
                        A JSON object with type and properties. Press Tab to
                        leave the editor.
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
              <SheetFooter className="border-t">
                <Button
                  type="button"
                  variant="outline"
                  onClick={requestClose}
                  disabled={mutation.isPending}
                >
                  Cancel
                </Button>
                <LoadingButton
                  id="tool-save"
                  type="submit"
                  data-testid="tool-save"
                  loading={mutation.isPending}
                  aria-disabled={!canSave || mutation.isPending}
                  className={cn(!canSave && "opacity-50")}
                  onClick={(event) => {
                    if (!canSave) {
                      event.preventDefault()
                    }
                  }}
                >
                  Save
                </LoadingButton>
              </SheetFooter>
            </form>
          </Form>
        </SheetContent>
      </Sheet>
      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent className="z-[60] sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Discard changes?</DialogTitle>
            <DialogDescription>
              You have unsaved changes. Are you sure you want to discard them?
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setConfirmOpen(false)}
            >
              Keep editing
            </Button>
            <Button
              type="button"
              variant="destructive"
              data-testid="discard-changes"
              onClick={discard}
            >
              Discard
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}

function HitlSwitch({
  checked,
  disabled,
  describedBy,
  onCheckedChange,
}: {
  checked: boolean
  disabled: boolean
  describedBy?: string
  onCheckedChange: (next: boolean) => void
}) {
  return (
    <button
      type="button"
      id="tool-hitl"
      role="switch"
      data-testid="tool-hitl"
      aria-checked={checked}
      aria-describedby={describedBy}
      disabled={disabled}
      onClick={() => {
        if (!disabled) {
          onCheckedChange(!checked)
        }
      }}
      className={cn(
        "focus-visible:ring-ring inline-flex h-5 w-9 shrink-0 items-center rounded-full border px-0.5 transition-colors focus-visible:ring-2 focus-visible:outline-none",
        checked ? "border-primary bg-primary" : "border-input bg-input",
        disabled && "cursor-not-allowed opacity-50",
      )}
    >
      <span
        className={cn(
          "bg-background pointer-events-none block size-4 rounded-full shadow-sm transition-transform",
          checked ? "translate-x-4" : "translate-x-0",
        )}
      />
    </button>
  )
}
