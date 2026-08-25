import { AxiosError } from "axios"

type HttpErrorShape = {
  response?: {
    status?: number
    data?: {
      detail?: unknown
    }
  }
}

export function getHttpErrorStatus(error: unknown): number | undefined {
  if (typeof error !== "object" || error === null) {
    return undefined
  }
  const status = (error as HttpErrorShape).response?.status
  return typeof status === "number" ? status : undefined
}

export function getHttpErrorDetail(error: unknown): unknown {
  if (typeof error !== "object" || error === null) {
    return undefined
  }
  return (error as HttpErrorShape).response?.data?.detail
}

export function isInvalidSessionError(error: unknown): boolean {
  const status = getHttpErrorStatus(error)
  const detail = getHttpErrorDetail(error)
  if (status === 401) {
    return true
  }
  if (status === 403 && detail === "Could not validate credentials") {
    return true
  }
  return status === 404 && detail === "User not found"
}

function extractErrorMessage(err: Error): string {
  if (err instanceof AxiosError) {
    const errDetail = (err.response?.data as any)?.detail
    if (Array.isArray(errDetail) && errDetail.length > 0) {
      return errDetail[0].msg
    }
    if (typeof errDetail === "string") {
      return errDetail
    }
    return err.message
  }
  return "Something went wrong."
}

export const handleError = function (this: (msg: string) => void, err: Error) {
  const errorMessage = extractErrorMessage(err)
  this(errorMessage)
}

export const getInitials = (name: string): string => {
  return name
    .split(" ")
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase()
}
