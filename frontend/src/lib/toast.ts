export interface NotificationOptions {
  type?: 'success' | 'error' | 'warning' | 'info'
  title?: string
  message: string
  duration?: number
  closable?: boolean
}

export interface ConfirmOptions {
  type?: 'success' | 'error' | 'warning' | 'info'
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
  positive?: boolean
}

// Injected by NotificationContainer via provide/inject
type AddNotifFn = (options: NotificationOptions) => string
type ShowConfirmFn = (options: ConfirmOptions) => Promise<boolean>

let _addNotification: AddNotifFn | null = null
let _showConfirm: ShowConfirmFn | null = null

/** Called by NotificationContainer on mount to wire up the API */
export function registerNotificationHandlers(
  addFn: AddNotifFn,
  confirmFn: ShowConfirmFn
) {
  _addNotification = addFn
  _showConfirm = confirmFn
}

function notify(options: NotificationOptions): string {
  if (_addNotification) {
    return _addNotification(options)
  }
  // Fallback: console only (SSR / before mount)
  console.log(`[${(options.type ?? 'info').toUpperCase()}] ${options.message}`)
  return ''
}

export const toast = {
  success: (message: string, duration?: number) =>
    notify({ message, type: 'success', duration }),
  error: (message: string, duration?: number) =>
    notify({ message, type: 'error', duration }),
  warning: (message: string, duration?: number) =>
    notify({ message, type: 'warning', duration }),
  info: (message: string, duration?: number) =>
    notify({ message, type: 'info', duration }),
}

export function confirmDialog(options: ConfirmOptions): Promise<boolean> {
  if (_showConfirm) {
    return _showConfirm(options)
  }
  // Fallback: native confirm
  return Promise.resolve(window.confirm(options.message))
}

// Backward compat — also re-export showToast for any stragglers
export function showToast(options: NotificationOptions & { type?: string }): void {
  notify(options as NotificationOptions)
}
