import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  const csrf = localStorage.getItem('csrf_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  if (csrf && ['post', 'patch', 'put', 'delete'].includes(config.method)) {
    config.headers['X-CSRF-Token'] = csrf
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('csrf_token')
      localStorage.removeItem('user')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  }
)

export default api
