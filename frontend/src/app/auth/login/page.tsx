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

const loginSchema = z.object({
  email: z.string().email('有効なメールアドレスを入力してください'),
  password: z.string().min(6, 'パスワードは6文字以上で入力してください'),
})

type LoginForm = z.infer<typeof loginSchema>

export default function LoginPage() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const router = useRouter()
  const { login, loading, isAuthenticated } = useAuth()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  })

  // 既にログイン済みの場合はダッシュボードにリダイレクト
  useEffect(() => {
    if (!loading && isAuthenticated) {
      router.push('/dashboard')
    }
  }, [loading, isAuthenticated, router])

  const onSubmit = async (data: LoginForm) => {
    setIsLoading(true)
    setError('')

    const result = await login(data.email, data.password)
    
    if (result.success) {
      router.push('/dashboard')
    } else {
      // より詳細なエラーメッセージの処理
      let errorMessage = result.error || 'ログインに失敗しました'
      
      if (errorMessage.includes('Incorrect email or password')) {
        errorMessage = 'メールアドレスまたはパスワードが間違っています。'
      } else if (errorMessage.includes('Inactive user')) {
        errorMessage = 'このアカウントは無効です。管理者にお問い合わせください。'
      } else if (errorMessage.includes('validation')) {
        errorMessage = '入力内容に誤りがあります。メールアドレスとパスワードを確認してください。'
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
            <CardTitle>ログイン</CardTitle>
            <CardDescription>
              アカウントにログインしてください
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
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
                {isLoading ? 'ログイン中...' : 'ログイン'}
              </Button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-sm text-gray-600">
                アカウントをお持ちでない方は{' '}
                <Link
                  href="/auth/register"
                  className="font-medium text-primary hover:underline"
                >
                  新規登録
                </Link>
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}