import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

// Types
export interface Project {
  id: string
  name: string
  description?: string
  chunking_strategy?: string
  chunking_config?: Record<string, any>
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
    api.post('/api/auth/login', { email, password }),
  register: (email: string, password: string, username: string) =>
    api.post('/api/auth/register', { email, password, username }),
  me: () => api.get('/api/auth/me'),
}

// Project API
export const projectApi = {
  getProjects: () => api.get('/api/projects'),
  getProject: (id: string) => api.get(`/api/projects/${id}`),
  createProject: (data: { 
    name: string; 
    description?: string;
    chunking_strategy?: string;
    chunking_config?: Record<string, any>;
  }) => api.post('/api/projects', data),
  updateProject: (id: string, data: { 
    name?: string; 
    description?: string;
    chunking_strategy?: string;
    chunking_config?: Record<string, any>;
  }) => api.put(`/api/projects/${id}`, data),
  deleteProject: (id: string) => api.delete(`/api/projects/${id}`),
  
  // Chunking configuration API
  updateChunkingConfig: (id: string, data: {
    chunking_strategy: string;
    chunking_config?: Record<string, any>;
  }) => api.put(`/api/projects/${id}/chunking-config`, data),
  getChunkingStrategies: () => api.get('/api/projects/chunking/strategies'),
  analyzeProjectContent: (id: string) => api.get(`/api/projects/${id}/chunking/analyze`),
}

// Source information for RAG responses
export interface SourceInfo {
  file_name: string;
  file_path: string;
  similarity_score: number;
  content_excerpt: string;
}

// Chat response with optional source information
export interface ChatResponse {
  message: string;
  provider: string;
  model: string;
  usage?: Record<string, any>;
  sources?: SourceInfo[];
}

// Chat API
export const chatApi = {
  sendMessage: (data: {
    project_id: string;
    message: string;
    provider: 'ollama' | 'lm_studio';
    model: string;
    context?: string;
  }) => api.post('/api/chat/send', data),
  
  // RAG-enhanced chat with source information
  sendRAGMessage: (data: {
    project_id: number;
    message: string;
    provider: 'ollama' | 'lm_studio';
    model: string;
    team_id?: number;
    context?: string;
  }) => api.post('/api/chat/send-rag', data),
  getChatHistory: (projectId: string) => api.get(`/api/chat/history/${projectId}`),
  checkLLMHealth: () => api.get('/api/chat/health'),
  
  // Model management
  getModels: (provider: 'ollama' | 'lm_studio') => 
    api.get(`/api/chat/models?provider=${provider}`),
  installModel: (data: { model_name: string; provider: string }) =>
    api.post('/api/chat/models/install', data),
  getInstallStatus: (taskId: string) =>
    api.get(`/api/chat/models/install/${taskId}`),
  cancelInstallTask: (taskId: string) =>
    api.post(`/api/chat/models/install/${taskId}/cancel`),
  deleteModel: (modelName: string, provider: string) =>
    api.delete(`/api/chat/models/${modelName}?provider=${provider}`),
  
  // Model presets
  getModelPresets: (provider: 'ollama' | 'lm_studio', params?: {
    category?: string;
    recommended_only?: boolean;
  }) => {
    const searchParams = new URLSearchParams({ provider });
    if (params?.category) searchParams.append('category', params.category);
    if (params?.recommended_only) searchParams.append('recommended_only', 'true');
    return api.get(`/api/chat/models/presets?${searchParams.toString()}`);
  },
  reloadModelPresets: () =>
    api.post('/api/chat/models/presets/reload'),
}

export default api