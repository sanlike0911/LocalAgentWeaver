'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Plus, LogOut, MessageCircle, Trash2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { projectApi, Project } from '@/utils/api'

const createProjectSchema = z.object({
  name: z.string().min(1, 'プロジェクト名は必須です'),
  description: z.string().optional(),
})

type CreateProjectForm = z.infer<typeof createProjectSchema>

export default function DashboardPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isCreating, setIsCreating] = useState(false)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [error, setError] = useState('')
  const router = useRouter()

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CreateProjectForm>({
    resolver: zodResolver(createProjectSchema),
  })

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) {
      router.push('/auth/login')
      return
    }
    
    fetchProjects()
  }, [router])

  const fetchProjects = async () => {
    try {
      const response = await projectApi.getProjects()
      setProjects(response.data)
    } catch (err) {
      setError('プロジェクトの取得に失敗しました')
    } finally {
      setIsLoading(false)
    }
  }

  const onCreateProject = async (data: CreateProjectForm) => {
    setIsCreating(true)
    setError('')

    try {
      const response = await projectApi.createProject({ name: data.name, description: data.description })
      setProjects([...projects, response.data])
      reset()
      setIsDialogOpen(false)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'プロジェクトの作成に失敗しました')
    } finally {
      setIsCreating(false)
    }
  }

  const onDeleteProject = async (projectId: string) => {
    if (!confirm('プロジェクトを削除しますか？')) return

    try {
      await projectApi.deleteProject(projectId)
      setProjects(projects.filter(p => p.id !== projectId))
    } catch (err) {
      setError('プロジェクトの削除に失敗しました')
    }
  }

  const onLogout = () => {
    localStorage.removeItem('token')
    router.push('/auth/login')
  }

  const openChat = (projectId: string) => {
    router.push(`/chat/${projectId}`)
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">LocalAgentWeaver</h1>
              <p className="text-gray-600">プロジェクト一覧</p>
            </div>
            <Button onClick={onLogout} variant="outline">
              <LogOut className="mr-2 h-4 w-4" />
              ログアウト
            </Button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded">
              {error}
            </div>
          )}

          <div className="mb-6">
            <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  新規プロジェクト
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>新規プロジェクト作成</DialogTitle>
                  <DialogDescription>
                    新しいプロジェクトを作成してください
                  </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleSubmit(onCreateProject)} className="space-y-4">
                  <div>
                    <Label htmlFor="name">プロジェクト名</Label>
                    <Input
                      id="name"
                      {...register('name')}
                      className="mt-1"
                    />
                    {errors.name && (
                      <p className="text-sm text-red-600 mt-1">{errors.name.message}</p>
                    )}
                  </div>

                  <div>
                    <Label htmlFor="description">説明（任意）</Label>
                    <Input
                      id="description"
                      {...register('description')}
                      className="mt-1"
                    />
                  </div>

                  <div className="flex justify-end space-x-2">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => setIsDialogOpen(false)}
                    >
                      キャンセル
                    </Button>
                    <Button type="submit" disabled={isCreating}>
                      {isCreating ? '作成中...' : '作成'}
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
          </div>

          {projects.length === 0 ? (
            <Card>
              <CardContent className="py-8">
                <div className="text-center">
                  <h3 className="text-lg font-medium text-gray-900">プロジェクトがありません</h3>
                  <p className="text-gray-600 mt-2">
                    最初のプロジェクトを作成してみましょう
                  </p>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {projects.map((project) => (
                <Card key={project.id} className="hover:shadow-md transition-shadow">
                  <CardHeader>
                    <CardTitle className="flex justify-between items-start">
                      <span className="truncate">{project.name}</span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onDeleteProject(project.id)}
                        className="text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </CardTitle>
                    {project.description && (
                      <CardDescription className="line-clamp-2">
                        {project.description}
                      </CardDescription>
                    )}
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between">
                      <p className="text-sm text-gray-600">
                        作成日: {new Date(project.created_at).toLocaleDateString('ja-JP')}
                      </p>
                      <Button
                        onClick={() => openChat(project.id)}
                        size="sm"
                      >
                        <MessageCircle className="mr-2 h-4 w-4" />
                        チャット
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}