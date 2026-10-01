import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Link as RouterLink, useNavigate } from "@tanstack/react-router"
import { useForm } from "react-hook-form"
import { z } from "zod"

import { LoginService, WorkspacesService } from "@/api"
import { AuthLayout } from "@/features/auth/AuthLayout"
import { setAccessToken } from "@/features/auth/session"
import { isLoggedIn } from "@/features/auth/useAuth"
import { invalidateWorkspaceSession } from "@/features/workspace/queries"
import { useCustomToast } from "@/shared/hooks/useCustomToast"
import { handleError } from "@/shared/lib/errors"
import { Button } from "@/shared/ui/button"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/shared/ui/form"
import { LoadingButton } from "@/shared/ui/loading-button"
import { PasswordInput } from "@/shared/ui/password-input"

const passwordSchema = z
  .object({
    new_password: z
      .string()
      .min(1, { message: "Password is required" })
      .min(8, { message: "Password must be at least 8 characters" }),
    confirm_password: z
      .string()
      .min(1, { message: "Password confirmation is required" }),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: "The passwords don't match",
    path: ["confirm_password"],
  })

type PasswordForm = z.infer<typeof passwordSchema>

const roleLabel = {
  admin: "Admin",
  editor: "Editor",
  viewer: "Viewer",
} as const

export function JoinWorkspace({
  token,
  decision,
}: {
  token: string
  decision?: "decline"
}) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const preview = useQuery({
    queryKey: ["workspace-invite", token],
    queryFn: async () =>
      (await WorkspacesService.readWorkspaceInvite({ query: { token } })).data,
    retry: false,
  })

  const form = useForm<PasswordForm>({
    resolver: zodResolver(passwordSchema),
    mode: "onBlur",
    defaultValues: { new_password: "", confirm_password: "" },
  })

  const goAfterDecision = () => {
    navigate({ to: isLoggedIn() ? "/dashboard" : "/login" })
  }

  const acceptMutation = useMutation({
    mutationFn: async (password?: string) => {
      await WorkspacesService.acceptWorkspaceInvite({
        body: password ? { token, password } : { token },
      })
      const email = preview.data?.email
      if (password && email) {
        const response = await LoginService.loginAccessToken({
          body: { username: email, password },
        })
        setAccessToken(response.data.access_token)
        await invalidateWorkspaceSession(queryClient)
      }
    },
    onSuccess: () => {
      showSuccessToast("Invite accepted")
      navigate({ to: isLoggedIn() ? "/dashboard" : "/login" })
    },
    onError: handleError.bind(showErrorToast),
  })

  const declineMutation = useMutation({
    mutationFn: () =>
      WorkspacesService.declineWorkspaceInvite({ body: { token } }),
    onSuccess: () => {
      showSuccessToast("Invite declined")
      goAfterDecision()
    },
    onError: handleError.bind(showErrorToast),
  })

  if (preview.isPending) {
    return (
      <AuthLayout>
        <p className="text-muted-foreground text-center text-sm">
          Loading invite…
        </p>
      </AuthLayout>
    )
  }

  if (preview.isError || !preview.data) {
    return (
      <AuthLayout>
        <div className="flex flex-col items-center gap-4 text-center">
          <h1 className="text-2xl font-bold">Invite is invalid</h1>
          <p className="text-muted-foreground text-sm">
            This link may have expired. Ask a workspace admin to send a new
            invite.
          </p>
          <Button asChild>
            <RouterLink to="/login">Go to login</RouterLink>
          </Button>
        </div>
      </AuthLayout>
    )
  }

  const invite = preview.data
  const alreadyAccepted = invite.status === "accepted"
  const alreadyDeclined = invite.status === "declined"

  if (alreadyAccepted) {
    return (
      <AuthLayout>
        <div className="flex flex-col items-center gap-4 text-center">
          <h1 className="text-2xl font-bold">Already a member</h1>
          <p className="text-muted-foreground text-sm">
            You already have access to {invite.workspace_name}.
          </p>
          <Button asChild>
            <RouterLink to={isLoggedIn() ? "/dashboard" : "/login"}>
              {isLoggedIn() ? "Open dashboard" : "Log in"}
            </RouterLink>
          </Button>
        </div>
      </AuthLayout>
    )
  }

  if (decision === "decline" || alreadyDeclined) {
    return (
      <AuthLayout>
        <div className="flex flex-col gap-6">
          <div className="flex flex-col items-center gap-2 text-center">
            <h1 className="text-2xl font-bold">Decline invite</h1>
            <p className="text-muted-foreground text-sm">
              {alreadyDeclined
                ? `You already declined ${invite.workspace_name}.`
                : `Decline the ${roleLabel[invite.role]} invite to ${invite.workspace_name}?`}
            </p>
          </div>
          {alreadyDeclined ? (
            <Button asChild className="w-full">
              <RouterLink to="/login">Go to login</RouterLink>
            </Button>
          ) : (
            <div className="flex flex-col gap-2">
              <LoadingButton
                className="w-full"
                data-testid="decline-invite-button"
                loading={declineMutation.isPending}
                onClick={() => declineMutation.mutate()}
                variant="destructive"
              >
                Decline invite
              </LoadingButton>
              <Button asChild variant="outline">
                <RouterLink
                  to="/join-workspace"
                  search={{ token, decision: undefined }}
                >
                  Go back
                </RouterLink>
              </Button>
            </div>
          )}
        </div>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout>
      <div className="flex flex-col gap-6">
        <div className="flex flex-col items-center gap-2 text-center">
          <h1 className="text-2xl font-bold">Join {invite.workspace_name}</h1>
          <p className="text-muted-foreground text-sm">
            You were invited as {roleLabel[invite.role]}.
          </p>
        </div>
        {invite.needs_password ? (
          <Form {...form}>
            <form
              className="grid gap-4"
              onSubmit={form.handleSubmit((data) =>
                acceptMutation.mutate(data.new_password),
              )}
            >
              <FormField
                control={form.control}
                name="new_password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Password</FormLabel>
                    <FormControl>
                      <PasswordInput
                        data-testid="join-password-input"
                        placeholder="Choose a password"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="confirm_password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Confirm password</FormLabel>
                    <FormControl>
                      <PasswordInput
                        data-testid="join-confirm-password-input"
                        placeholder="Confirm password"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <LoadingButton
                className="w-full"
                data-testid="accept-invite-button"
                loading={acceptMutation.isPending}
                type="submit"
              >
                Accept invite
              </LoadingButton>
            </form>
          </Form>
        ) : (
          <LoadingButton
            className="w-full"
            data-testid="accept-invite-button"
            loading={acceptMutation.isPending}
            onClick={() => acceptMutation.mutate(undefined)}
          >
            Accept invite
          </LoadingButton>
        )}
        <Button asChild variant="ghost">
          <RouterLink
            to="/join-workspace"
            search={{ token, decision: "decline" }}
          >
            Decline this invite
          </RouterLink>
        </Button>
      </div>
    </AuthLayout>
  )
}
