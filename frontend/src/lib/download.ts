function sanitizeFileName(value: string) {
  return value.replace(/[<>:"/\\|?*\u0000-\u001F]+/g, '-').replace(/\s+/g, '-')
}

export function downloadJson(filename: string, payload: unknown) {
  const serialized = JSON.stringify(payload, null, 2)
  const blob = new Blob([serialized], { type: 'application/json;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')

  link.href = url
  link.download = sanitizeFileName(filename)
  link.click()

  URL.revokeObjectURL(url)
}
