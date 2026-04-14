export interface BacktestReportExportOptions {
  jobId: string
  title: string
  filename?: string
}

function sanitizeFileName(value: string): string {
  return value.replace(/[<>:"/\\|?*\u0000-\u001F]+/g, '-').replace(/\s+/g, '-')
}

function triggerBlobDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')

  link.href = url
  link.download = sanitizeFileName(filename)
  link.click()

  URL.revokeObjectURL(url)
}

function copyCanvasContent(sourceRoot: HTMLElement, clonedRoot: HTMLElement): void {
  const sourceCanvases = Array.from(sourceRoot.querySelectorAll('canvas'))
  const clonedCanvases = Array.from(clonedRoot.querySelectorAll('canvas'))

  sourceCanvases.forEach((canvas, index) => {
    const clonedCanvas = clonedCanvases[index]
    if (!clonedCanvas) {
      return
    }

    try {
      const image = document.createElement('img')
      image.src = canvas.toDataURL('image/png')
      image.alt = ''
      image.className = clonedCanvas.className
      image.style.cssText = clonedCanvas.getAttribute('style') || ''
      image.width = canvas.width
      image.height = canvas.height
      clonedCanvas.replaceWith(image)
    } catch {
      // Ignore canvas export failures and leave the cloned canvas in place.
    }
  })
}

function removeIgnoredNodes(root: HTMLElement): void {
  root.querySelectorAll('[data-export-ignore="true"]').forEach((node) => node.remove())
}

function collectDocumentStyles(): string {
  const styleBlocks: string[] = []

  for (const sheet of Array.from(document.styleSheets)) {
    try {
      const rules = Array.from(sheet.cssRules)
      if (!rules.length) {
        continue
      }
      styleBlocks.push(rules.map((rule) => rule.cssText).join('\n'))
    } catch {
      // Skip inaccessible stylesheets.
    }
  }

  return styleBlocks.join('\n')
}

export function buildBacktestReportHtml(root: HTMLElement, options: BacktestReportExportOptions): string {
  const clonedRoot = root.cloneNode(true) as HTMLElement
  removeIgnoredNodes(clonedRoot)
  copyCanvasContent(root, clonedRoot)

  const styles = collectDocumentStyles()
  const title = options.title || `Backtest Report ${options.jobId}`

  return `<!doctype html>
<html lang="${document.documentElement.lang || 'zh-CN'}">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>${title}</title>
    <style>${styles}</style>
    <style>
      body {
        margin: 0;
      }
    </style>
  </head>
  <body>
    ${clonedRoot.outerHTML}
  </body>
</html>`
}

export function downloadBacktestReportAsHtml(root: HTMLElement, options: BacktestReportExportOptions): void {
  const html = buildBacktestReportHtml(root, options)
  const blob = new Blob([html], { type: 'text/html;charset=utf-8' })
  const filename = options.filename || `backtest-report-${options.jobId}.html`

  triggerBlobDownload(blob, filename)
}

export async function printBacktestReportAsPdf(
  root: HTMLElement,
  options: BacktestReportExportOptions,
): Promise<void> {
  const html = buildBacktestReportHtml(root, options)
  const token = typeof window !== 'undefined' ? localStorage.getItem('qyquant-token') : null
  const response = await fetch(`/api/v1/backtest/${options.jobId}/export/pdf`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({
      html,
      filename: options.filename || `backtest-report-${options.jobId}.pdf`,
    }),
  })

  if (!response.ok) {
    throw new Error(`Failed to export PDF (${response.status})`)
  }

  const blob = await response.blob()
  const filename = options.filename || `backtest-report-${options.jobId}.pdf`
  triggerBlobDownload(blob, filename)
}
