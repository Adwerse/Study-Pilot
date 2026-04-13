import WebApp from '@twa-dev/sdk'

export function getInitData(): string {
  return WebApp.initData
}

export function getTelegramUser() {
  return WebApp.initDataUnsafe.user
}

export function expandApp() {
  WebApp.expand()
}

export function closeMiniApp() {
  WebApp.close()
}

export function ready() {
  WebApp.ready()
}