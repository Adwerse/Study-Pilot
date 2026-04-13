import axios from 'axios'
import { getInitData } from './telegram'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
})

api.interceptors.request.use((config) => {
  const initData = getInitData()
  if (initData) {
    config.headers.Authorization = `tma ${initData}`
  }
  return config
})

export default api