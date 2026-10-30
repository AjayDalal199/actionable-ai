import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Trash2 } from "lucide-react"
import { useState } from "react"
import { useForm } from "react-hook-form"

import { KnowledgeService } from "@/api"
import { documentKeys } from "@/features/knowledge/queries"
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
import { LoadingButton } from "@/shared/ui/loading-button"

export function DeleteDocument({
  id,
  filename,
}: {
  id: string
  filename: string
}) {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const { handleSubmit } = useForm()

  const mutation = useMutation({
    mutationFn: () =>
      KnowledgeService.removeDocument({ path: { document_id: id } }),
    onSuccess: () => {
      showSuccessToast("Document deleted")
      setIsOpen(false)
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: documentKeys.all })
    },
  })

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setIsOpen(true)}
        data-testid={`delete-document-${id}`}
      >
        <Trash2 />
        Delete
      </Button>
      <DialogContent className="sm:max-w-md">
        <form onSubmit={handleSubmit(() => mutation.mutate())}>
          <DialogHeader>
            <DialogTitle>Delete document</DialogTitle>
            <DialogDescription>
              {filename} and its chunks will be permanently deleted. This cannot
              be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="mt-4">
            <DialogClose asChild>
              <Button variant="outline" disabled={mutation.isPending}>
                Cancel
              </Button>
            </DialogClose>
            <LoadingButton
              variant="destructive"
              type="submit"
              loading={mutation.isPending}
            >
              Delete
            </LoadingButton>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
