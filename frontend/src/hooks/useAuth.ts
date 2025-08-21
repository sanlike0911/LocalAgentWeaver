'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { authApi } from '@/utils/api'

export interface User {
  id: string
  email: string
  username: string
  is_active: boolean
  created_at: string
  updated_at?: string
}

export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const router = useRouter()

  const checkAuth = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      
      if (!token) {
        setUser(null)
        setIsAuthenticated(false)
        return false
      }

      const response = await authApi.me()
      setUser(response.data)
      setIsAuthenticated(true)
      return true
    } catch (error) {
      // Token is invalid or expired
      localStorage.removeItem('token')
      setUser(null)
      setIsAuthenticated(false)
      return false
    } finally {
      setLoading(false)
    }
  }

  const login = async (email: string, password: string) => {
    try {
      const response = await authApi.login(email, password)
      localStorage.setItem('token', response.data.access_token)
      await checkAuth()
      return { success: true, data: response.data }
    } catch (error: any) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'ログインに失敗しました'
      }
    }
  }

  const register = async (email: string, password: string, username: string) => {
    try {
      const response = await authApi.register(email, password, username)
      return { success: true, data: response.data }
    } catch (error: any) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'アカウント作成に失敗しました'
      }
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    setUser(null)
    setIsAuthenticated(false)
    router.push('/auth/login')
  }

  const requireAuth = () => {
    if (!loading && !isAuthenticated) {
      router.push('/auth/login')
      return false
    }
    return true
  }

  useEffect(() => {
    checkAuth()
  }, [])

  return {
    user,
    loading,
    isAuthenticated,
    login,
    register,
    logout,
    requireAuth,
    checkAuth
  }
}