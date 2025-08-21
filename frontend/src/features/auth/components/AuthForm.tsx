'use client'

import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { AuthAPI, RegisterData, LoginData, registerSchema, loginSchema } from '../api'

interface AuthFormProps {
  onSuccess?: (user: any) => void
}

export function AuthForm({ onSuccess }: AuthFormProps) {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: ''
  })
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})

  const validateForm = () => {
    const schema = mode === 'login' ? loginSchema : registerSchema
    const result = schema.safeParse(formData)
    
    if (!result.success) {
      const errors: Record<string, string> = {}
      result.error.errors.forEach((error) => {
        errors[error.path[0] as string] = error.message
      })
      setValidationErrors(errors)
      return false
    }
    
    setValidationErrors({})
    return true
  }

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    // Clear validation error for this field when user starts typing
    if (validationErrors[field]) {
      setValidationErrors(prev => ({ ...prev, [field]: '' }))
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!validateForm()) {
      return
    }

    setLoading(true)

    try {
      if (mode === 'register') {
        const user = await AuthAPI.register(formData as RegisterData)
        alert('アカウントが正常に作成されました！')
        setMode('login') // Switch to login after successful registration
      } else {
        const tokenResponse = await AuthAPI.login({
          email: formData.email,
          password: formData.password
        } as LoginData)
        
        // Store token in localStorage (in production, consider more secure storage)
        localStorage.setItem('auth_token', tokenResponse.access_token)
        
        // Get user info
        const user = await AuthAPI.getCurrentUser(tokenResponse.access_token)
        onSuccess?.(user)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '予期しないエラーが発生しました')
    } finally {
      setLoading(false)
    }
  }

  const isLogin = mode === 'login'

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <CardTitle>{isLogin ? 'ログイン' : 'アカウント作成'}</CardTitle>
        <CardDescription>
          {isLogin ? 'アカウントにログインしてください' : '新しいアカウントを作成してください'}
        </CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-4">
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}
          
          <div className="space-y-2">
            <Label htmlFor="email">メールアドレス</Label>
            <Input
              id="email"
              type="email"
              value={formData.email}
              onChange={(e) => handleInputChange('email', e.target.value)}
              placeholder="your@example.com"
              disabled={loading}
            />
            {validationErrors.email && (
              <p className="text-sm text-red-600">{validationErrors.email}</p>
            )}
          </div>

          {!isLogin && (
            <div className="space-y-2">
              <Label htmlFor="username">ユーザー名</Label>
              <Input
                id="username"
                type="text"
                value={formData.username}
                onChange={(e) => handleInputChange('username', e.target.value)}
                placeholder="ユーザー名を入力"
                disabled={loading}
              />
              {validationErrors.username && (
                <p className="text-sm text-red-600">{validationErrors.username}</p>
              )}
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="password">パスワード</Label>
            <Input
              id="password"
              type="password"
              value={formData.password}
              onChange={(e) => handleInputChange('password', e.target.value)}
              placeholder="パスワードを入力"
              disabled={loading}
            />
            {validationErrors.password && (
              <p className="text-sm text-red-600">{validationErrors.password}</p>
            )}
          </div>
        </CardContent>
        <CardFooter className="flex flex-col space-y-4">
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? '処理中...' : (isLogin ? 'ログイン' : 'アカウント作成')}
          </Button>
          
          <div className="text-center">
            <button
              type="button"
              onClick={() => {
                setMode(isLogin ? 'register' : 'login')
                setError('')
                setValidationErrors({})
                setFormData({ email: '', username: '', password: '' })
              }}
              className="text-sm text-blue-600 hover:text-blue-800 underline"
              disabled={loading}
            >
              {isLogin ? 'アカウントをお持ちでない方はこちら' : '既にアカウントをお持ちの方はこちら'}
            </button>
          </div>
        </CardFooter>
      </form>
    </Card>
  )
}