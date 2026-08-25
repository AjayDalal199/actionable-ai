import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useForm } from "react-hook-form"
import { z } from "zod"

import { WorkspacesService } from "@/api"
import {
  invalidateWorkspaceSession,
  workspaceKeys,
} from "@/features/workspace/queries"
import { useCustomToast } from "@/shared/hooks/useCustomToast"
import { handleError } from "@/shared/lib/errors"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/shared/ui/form"
import { Input } from "@/shared/ui/input"
import { LoadingButton } from "@/shared/ui/loading-button"

const formSchema = z.object({
  name: z
    .string()
    .trim()
    .min(1, { message: "Workspace name is required" })
    .max(255, { message: "Workspace name must be 255 characters or fewer" }),
})

type FormData = z.infer<typeof formSchema>

export function CreateWorkspaceForm({ onCreated }: { onCreated?: () => void }) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      name: "",
    },
  })

  const mutation = useMutation({
    mutationFn: (data: FormData) =>
      WorkspacesService.createWorkspace({ body: data }),
    onSuccess: (response) => {
      queryClient.setQueryData(workspaceKeys.current, response.data)
      showSuccessToast("Workspace created")
      form.reset()
      onCreated?.()
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      void invalidateWorkspaceSession(queryClient)
    },
  })

  return (
    <Form {...form}>
      <form
        className="flex flex-col gap-3 sm:flex-row sm:items-end"
        onSubmit={form.handleSubmit((data) => mutation.mutate(data))}
      >
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem className="flex-1">
              <FormLabel>Workspace name</FormLabel>
              <FormControl>
                <Input
                  data-testid="create-workspace-name-input"
                  placeholder="Acme Corp"
                  type="text"
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <LoadingButton
          data-testid="create-workspace-button"
          loading={mutation.isPending}
          type="submit"
        >
          Create workspace
        </LoadingButton>
      </form>
    </Form>
  )
}
