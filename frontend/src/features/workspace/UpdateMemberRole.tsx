import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Pencil } from "lucide-react"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import type { WorkspaceMemberPublic, WorkspaceRole } from "@/api"
import { WorkspacesService } from "@/api"
import { invalidateWorkspaceSession } from "@/features/workspace/queries"
import { useCustomToast } from "@/shared/hooks/useCustomToast"
import { handleError } from "@/shared/lib/errors"
import { Button } from "@/shared/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog"
import { DropdownMenuItem } from "@/shared/ui/dropdown-menu"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/shared/ui/form"
import { LoadingButton } from "@/shared/ui/loading-button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/ui/select"

const formSchema = z.object({
  role: z.enum(["admin", "editor", "viewer"]),
})

type FormData = z.infer<typeof formSchema>

export function UpdateMemberRole({
  member,
  onSuccess,
}: {
  member: WorkspaceMemberPublic
  onSuccess: () => void
}) {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: { role: member.role },
  })

  const mutation = useMutation({
    mutationFn: (role: WorkspaceRole) =>
      WorkspacesService.updateWorkspaceMember({
        path: { user_id: member.id },
        body: { role },
      }),
    onSuccess: () => {
      showSuccessToast("Role updated")
      setIsOpen(false)
      onSuccess()
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      void invalidateWorkspaceSession(queryClient)
    },
  })

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuItem
        onSelect={(event) => event.preventDefault()}
        onClick={() => setIsOpen(true)}
      >
        <Pencil />
        Change role
      </DropdownMenuItem>
      <DialogContent className="sm:max-w-md">
        <Form {...form}>
          <form
            onSubmit={form.handleSubmit((data) => mutation.mutate(data.role))}
          >
            <DialogHeader>
              <DialogTitle>Change role</DialogTitle>
              <DialogDescription>
                Update {member.email}'s role in this workspace.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <FormField
                control={form.control}
                name="role"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Role</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger
                          className="w-full"
                          data-testid="update-member-role"
                        >
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="admin">Admin</SelectItem>
                        <SelectItem value="editor">Editor</SelectItem>
                        <SelectItem value="viewer">Viewer</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            <DialogFooter>
              <DialogClose asChild>
                <Button variant="outline" disabled={mutation.isPending}>
                  Cancel
                </Button>
              </DialogClose>
              <LoadingButton loading={mutation.isPending} type="submit">
                Save
              </LoadingButton>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
