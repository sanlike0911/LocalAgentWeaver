'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'

export default function Home() {
  const { loading, isAuthenticated } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading) {
      if (isAuthenticated) {
        // ログイン済みの場合はダッシュボードへリダイレクト
        router.push('/dashboard')
      } else {
        // 未ログインの場合はログイン画面へリダイレクト
        router.push('/auth/login')
      }
    }
  }, [loading, isAuthenticated, router])

  // 認証状態チェック中のローディング画面
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
        <p className="text-gray-600">読み込み中...</p>
      </div>
    </div>
  )
}