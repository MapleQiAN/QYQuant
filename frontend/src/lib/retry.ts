export async function retry<T>(
  fn: () => Promise<T>,
  options: { retries: number; delays: number[] }
): Promise<T> {
  const { retries, delays } = options
  let lastError: unknown

  for (let attempt = 0; attempt < retries; attempt += 1) {
    try {
      return await fn()
    } catch (error) {
      lastError = error
      const delay = delays[attempt] ?? delays[delays.length - 1] ?? 0
      if (attempt < retries - 1 && delay > 0) {
        await new Promise((resolve) => setTimeout(resolve, delay))
      }
    }
  }

  throw lastError
}
