export function normalizeError(error: any): { status?: number; code?: string; message: string } {
  const status = error?.response?.status
  const backendError = error?.response?.data?.error
  const message =
    backendError?.message ||
    error?.response?.data?.message ||
    error?.message ||
    'Unknown error'
  const code = backendError?.code

  return { status, code, message }
}
