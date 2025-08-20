import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Types
export interface Project {
  id: string
  name: string
  description?: string
  created_at: string
  updated_at: string
}

export interface User {
  id: string
  email: string
  username: string
}

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle common errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/auth/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  register: (email: string, password: string, username: string) =>
    api.post('/auth/register', { email, password, username }),
  me: () => api.get('/auth/me'),
}

// Project API
export const projectApi = {
  getProjects: () => api.get('/projects'),
  getProject: (id: string) => api.get(`/projects/${id}`),
  createProject: (data: { name: string; description?: string }) =>
    api.post('/projects', data),
  updateProject: (id: string, data: { name: string; description?: string }) =>
    api.put(`/projects/${id}`, data),
  deleteProject: (id: string) => api.delete(`/projects/${id}`),
}

// Chat API
export const chatApi = {
  sendMessage: (data: {
    project_id: string;
    message: string;
    provider: 'ollama' | 'lm_studio';
    model: string;
    context?: string;
  }) => api.post('/chat/send', data),
  getChatHistory: (projectId: string) => api.get(`/chat/history/${projectId}`),
}

export default api