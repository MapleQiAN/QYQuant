import { readFile } from 'node:fs/promises'
import path from 'node:path'
import process from 'node:process'

const root = process.cwd()
const files = [
  'src/data/plans.ts',
  'src/i18n/messages/zh.ts',
  'src/i18n/messages/en.ts',
  'src/router/index.ts',
  'src/views/CheckoutView.vue',
  'src/views/PricingView.vue',
  'src/components/NotificationPanel.vue',
]

const mojibakeSignatures = [
  '閫傚悎',
  '鍩虹',
  '鍥炴祴',
  '缁╂晥',
  '鏃犻檺',
  '鑷畾',
  '浼樺厛',
  '绛栫暐',
  '鏁版嵁',
  '鐮旂┒',
]

const failures = []
const cjkRegex = /[\u3400-\u9FFF]/

for (const relativePath of files) {
  const fullPath = path.join(root, relativePath)
  const text = await readFile(fullPath, 'utf8')

  if (text.includes('\uFFFD')) {
    failures.push(`${relativePath}: contains replacement character U+FFFD`)
  }

  for (const signature of mojibakeSignatures) {
    if (text.includes(signature)) {
      failures.push(`${relativePath}: contains mojibake signature "${signature}"`)
      break
    }
  }

  if (relativePath === 'src/data/plans.ts' && cjkRegex.test(text)) {
    failures.push(`${relativePath}: contains localized copy outside i18n`)
  }
}

if (failures.length > 0) {
  console.error('i18n/encoding check failed:')
  for (const failure of failures) {
    console.error(`- ${failure}`)
  }
  process.exit(1)
}

console.log('i18n/encoding check passed')
