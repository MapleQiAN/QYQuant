import { createHttpClient } from './http'
import type { Post } from '../types/Post'

const client = createHttpClient()

export function fetchHot(): Promise<Post[]> {
  return client.request({ method: 'get', url: '/forum/hot' })
}
