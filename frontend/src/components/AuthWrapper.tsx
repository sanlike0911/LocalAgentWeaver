'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'

interface AuthWrapperProps {
  children: React.ReactNode
  requireAuth?: boolean
  redirectTo?: string
}

export default function AuthWrapper({ 
  children, 
  requireAuth = true,
  redirectTo = '/auth/login'
}: AuthWrapperProps) {
  const { loading, isAuthenticated } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading && requireAuth && !isAuthenticated) {
      router.push(redirectTo)
    }
  }, [loading, isAuthenticated, requireAuth, redirectTo, router])

  // Show loading while checking authentication
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-gray-600">認証状態を確認中...</p>
        </div>
      </div>
    )
  }

  // If auth is required but user is not authenticated, don't render children
  // (redirect will happen in useEffect)
  if (requireAuth && !isAuthenticated) {
    return null
  }

  return <>{children}</>
}