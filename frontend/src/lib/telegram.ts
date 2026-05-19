import WebApp from '@twa-dev/sdk'

export const tg = WebApp

export function getInitData(): string {
  return WebApp.initData
}

export function getTelegramUser() {
  return WebApp.initDataUnsafe?.user ?? null
}

export function ready() {
  WebApp.ready()
}

export function expand() {
  WebApp.expand()
}

export function syncViewportCssVars() {
  const viewportHeight = WebApp.viewportStableHeight || WebApp.viewportHeight || window.innerHeight
  document.documentElement.style.setProperty('--tg-viewport-height', `${viewportHeight}px`)
}

export function subscribeViewportChanges(handler: () => void) {
  WebApp.onEvent?.('viewportChanged', handler)

  return () => {
    WebApp.offEvent?.('viewportChanged', handler)
  }
}
