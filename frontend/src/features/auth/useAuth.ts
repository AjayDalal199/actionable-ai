import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"

import {
  type Body_login_login_access_token as AccessToken,
  LoginService,
  type UserRegister,
  UsersService,
} from "@/api"
import { userKeys } from "@/features/admin/queries"
import { authKeys, currentUserQueryOptions } from "@/features/auth/queries"
import {
  clearAccessToken,
  isLoggedIn,
  setAccessToken,
} from "@/features/auth/session"
import { useCustomToast } from "@/shared/hooks/useCustomToast"
import { handleError } from "@/shared/lib/errors"

export { isLoggedIn } from "@/features/auth/session"

export const useAuth = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showErrorToast } = useCustomToast()

  const { data: user } = useQuery({
    ...currentUserQueryOptions,
    enabled: isLoggedIn(),
  })

  const login = async (data: AccessToken) => {
    const response = await LoginService.loginAccessToken({
      body: data,
    })
    setAccessToken(response.data.access_token)
  }

  const signUpMutation = useMutation({
    mutationFn: async (data: UserRegister) => {
      await UsersService.registerUser({ body: data })
      await login({
        username: data.email,
        password: data.password,
      })
    },
    onSuccess: () => {
      navigate({ to: "/dashboard" })
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: userKeys.all })
    },
  })

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: () => {
      navigate({ to: "/dashboard" })
    },
    onError: handleError.bind(showErrorToast),
  })

  const logout = () => {
    clearAccessToken()
    queryClient.removeQueries({ queryKey: authKeys.currentUser })
    navigate({ to: "/login" })
  }

  return {
    signUpMutation,
    loginMutation,
    logout,
    user,
  }
}
