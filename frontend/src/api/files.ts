import { createHttpClient } from './http'

const client = createHttpClient()

export interface UploadedPublicImage {
  id: string
  url: string
}

export function uploadPublicImage(file: File): Promise<UploadedPublicImage> {
  const form = new FormData()
  form.append('file', file)

  return client.request({
    method: 'post',
    url: '/files',
    data: form,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}
