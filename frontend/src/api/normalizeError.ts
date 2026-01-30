export function normalizeError(error: any): { status?: number; message: string } {
  const status = error?.response?.status
  const message = error?.response?.data?.message || error?.message || 'Unknown error'

  return { status, message }
}
