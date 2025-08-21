import { z } from 'zod'

// API Response Types
export interface User {
  id: number
  email: string
  username: string
  is_active: boolean
  created_at: string
  updated_at?: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

// Validation Schemas
export const registerSchema = z.object({
  email: z.string().email('有効なメールアドレスを入力してください'),
  username: z.string().min(3, 'ユーザー名は3文字以上である必要があります'),
  password: z.string().min(8, 'パスワードは8文字以上である必要があります'),
})

export const loginSchema = z.object({
  email: z.string().email('有効なメールアドレスを入力してください'),
  password: z.string().min(1, 'パスワードを入力してください'),
})

export type RegisterData = z.infer<typeof registerSchema>
export type LoginData = z.infer<typeof loginSchema>

// API Client
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

// Debug log - 環境変数の読み込み確認
console.log('=== Environment Variables Debug ===')
console.log('NODE_ENV:', process.env.NODE_ENV)
console.log('NEXT_PUBLIC_API_BASE_URL:', process.env.NEXT_PUBLIC_API_BASE_URL)
console.log('Final API_BASE_URL:', API_BASE_URL)
console.log('All NEXT_PUBLIC_ vars:', Object.keys(process.env).filter(key => key.startsWith('NEXT_PUBLIC_')))
console.log('=======================================')

export class AuthAPI {
  static async register(data: RegisterData): Promise<User> {
    debugger; // ブレイクポイント
    const url = `${API_BASE_URL}/api/auth/register`
    console.log('Registration URL:', url)
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Registration failed' }))
      throw new Error(error.detail || 'Registration failed')
    }

    return response.json()
  }

  static async login(data: LoginData): Promise<TokenResponse> {
    debugger; // ブレイクポイント
    const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Login failed' }))
      throw new Error(error.detail || 'Login failed')
    }

    return response.json()
  }

  static async getCurrentUser(token: string): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to fetch user info' }))
      throw new Error(error.detail || 'Failed to fetch user info')
    }

    return response.json()
  }
}