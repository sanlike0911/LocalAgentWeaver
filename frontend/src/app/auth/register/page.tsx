'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useAuth } from '@/hooks/useAuth'

const registerSchema = z.object({
  username: z.string().min(2, 'ユーザー名は2文字以上で入力してください'),
  email: z.string().email('有効なメールアドレスを入力してください'),
  password: z.string().min(6, 'パスワードは6文字以上で入力してください'),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: 'パスワードが一致しません',
  path: ['confirmPassword'],
})

type RegisterForm = z.infer<typeof registerSchema>

export default function RegisterPage() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const router = useRouter()
  const { register: registerUser, login, loading, isAuthenticated } = useAuth()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
  })

  // 既にログイン済みの場合はダッシュボードにリダイレクト
  useEffect(() => {
    if (!loading && isAuthenticated) {
      router.push('/dashboard')
    }
  }, [loading, isAuthenticated, router])

  const onSubmit = async (data: RegisterForm) => {
    setIsLoading(true)
    setError('')
    setSuccess('')

    // ユーザー登録
    const registerResult = await registerUser(data.email, data.password, data.username)
    
    if (registerResult.success) {
      setSuccess('アカウントが正常に作成されました！自動的にログインしています...')
      
      // 自動ログイン
      setTimeout(async () => {
        const loginResult = await login(data.email, data.password)
        if (loginResult.success) {
          router.push('/dashboard')
        } else {
          setSuccess('')
          setError('アカウント作成は成功しましたが、ログインに失敗しました。ログインページからログインしてください。')
        }
      }, 2000)
    } else {
      setSuccess('')
      // より詳細なエラーメッセージの処理
      let errorMessage = registerResult.error || 'アカウント作成に失敗しました'
      
      if (errorMessage.includes('Email already registered')) {
        errorMessage = 'このメールアドレスは既に登録されています。ログインページからログインしてください。'
      } else if (errorMessage.includes('validation')) {
        errorMessage = '入力内容に誤りがあります。入力内容を確認してください。'
      } else if (errorMessage.includes('Network Error')) {
        errorMessage = 'ネットワークエラーが発生しました。接続を確認してください。'
      }
      
      setError(errorMessage)
    }
    
    setIsLoading(false)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">LocalAgentWeaver</h1>
          <p className="mt-2 text-gray-600">AIエージェントプラットフォーム</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>新規登録</CardTitle>
            <CardDescription>
              新しいアカウントを作成してください
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div>
                <Label htmlFor="username">ユーザー名</Label>
                <Input
                  id="username"
                  type="text"
                  {...register('username')}
                  className="mt-1"
                />
                {errors.username && (
                  <p className="text-sm text-red-600 mt-1">{errors.username.message}</p>
                )}
              </div>

              <div>
                <Label htmlFor="email">メールアドレス</Label>
                <Input
                  id="email"
                  type="email"
                  {...register('email')}
                  className="mt-1"
                />
                {errors.email && (
                  <p className="text-sm text-red-600 mt-1">{errors.email.message}</p>
                )}
              </div>

              <div>
                <Label htmlFor="password">パスワード</Label>
                <Input
                  id="password"
                  type="password"
                  {...register('password')}
                  className="mt-1"
                />
                {errors.password && (
                  <p className="text-sm text-red-600 mt-1">{errors.password.message}</p>
                )}
              </div>

              <div>
                <Label htmlFor="confirmPassword">パスワード（確認）</Label>
                <Input
                  id="confirmPassword"
                  type="password"
                  {...register('confirmPassword')}
                  className="mt-1"
                />
                {errors.confirmPassword && (
                  <p className="text-sm text-red-600 mt-1">{errors.confirmPassword.message}</p>
                )}
              </div>

              {success && (
                <div className="bg-green-50 border border-green-200 text-green-600 px-4 py-3 rounded">
                  {success}
                </div>
              )}

              {error && (
                <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded">
                  {error}
                </div>
              )}

              <Button
                type="submit"
                className="w-full"
                disabled={isLoading}
              >
                {isLoading ? 'アカウント作成中...' : 'アカウント作成'}
              </Button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-sm text-gray-600">
                既にアカウントをお持ちの方は{' '}
                <Link
                  href="/auth/login"
                  className="font-medium text-primary hover:underline"
                >
                  ログイン
                </Link>
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}