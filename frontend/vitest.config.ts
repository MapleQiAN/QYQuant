import dns from 'node:dns'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vitest/config'

const originalLookup = dns.lookup
const originalPromisesLookup = dns.promises.lookup
dns.lookup = ((hostname: string, options: any, callback?: any) => {
  if (hostname === 'localhost') {
    const result = { address: '127.0.0.1', family: 4 }
    if (typeof options === 'function') {
      return options(null, result.address, result.family)
    }
    if (callback) {
      return callback(null, result.address, result.family)
    }
    return Promise.resolve(result)
  }

  return originalLookup(hostname, options as any, callback)
}) as typeof dns.lookup

dns.promises.lookup = (async (hostname: string, options?: any) => {
  if (hostname === 'localhost') {
    return { address: '127.0.0.1', family: 4 }
  }

  return originalPromisesLookup(hostname, options)
}) as typeof dns.promises.lookup

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'jsdom',
    environmentOptions: {
      jsdom: {
        url: 'http://127.0.0.1/',
      },
    },
  }
})
