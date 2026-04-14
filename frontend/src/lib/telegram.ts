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
