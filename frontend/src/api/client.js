// src/api/client.js — Axios instance with JWT auth interceptor
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

const client = axios.create({ baseURL: API_BASE })

// Attach JWT from localStorage on every request
client.interceptors.request.use((config) => {
    const token = localStorage.getItem('medscan_token')
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
})

// Redirect to login on 401
client.interceptors.response.use(
    (res) => res,
    (err) => {
        if (err.response?.status === 401) {
            localStorage.removeItem('medscan_token')
            window.location.href = '/login'
        }
        return Promise.reject(err)
    }
)

export default client
