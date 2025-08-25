'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Plus, MessageCircle, Trash2, Search } from 'lucide-react'

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
import AuthWrapper from '@/components/AuthWrapper'

const createProjectSchema = z.object({
  name: z.string().min(1, 'プロジェクト名は必須です'),
  description: z.string().optional(),
})

type CreateProjectForm = z.infer<typeof createProjectSchema>

function DashboardPageContent() {
  const [projects, setProjects] = useState<Project[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isCreating, setIsCreating] = useState(false)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [error, setError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
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
    fetchProjects()
  }, [])

  const fetchProjects = async () => {
    try {
      const response = await projectApi.getProjects()
      // プロジェクトが配列でない場合でも正常に処理する
      if (response.data && Array.isArray(response.data.projects)) {
        setProjects(response.data.projects)
      } else if (response.data && Array.isArray(response.data)) {
        setProjects(response.data)
      } else {
        setProjects([])
      }
      setError('') // エラーをクリア
    } catch (err: any) {
      console.error('Failed to fetch projects:', err)
      // 404エラーの場合はプロジェクトが0件として処理
      if (err.response?.status === 404) {
        setProjects([])
        setError('')
      } else {
        setError('プロジェクトの取得に失敗しました')
      }
    } finally {
      setIsLoading(false)
    }
  }

  const onCreateProject = async (data: CreateProjectForm) => {
    setIsCreating(true)
    setError('')
    setSuccessMessage('')

    try {
      const response = await projectApi.createProject({ name: data.name, description: data.description })
      setProjects([...projects, response.data])
      setSuccessMessage('プロジェクトが正常に作成されました')
      reset()
      setIsDialogOpen(false)
      
      // 成功メッセージを3秒後に消去
      setTimeout(() => setSuccessMessage(''), 3000)
    } catch (err: any) {
      console.error('Failed to create project:', err)
      setError(err.response?.data?.detail || 'プロジェクトの作成に失敗しました')
    } finally {
      setIsCreating(false)
    }
  }

  const onDeleteProject = async (projectId: string) => {
    if (!confirm('プロジェクトを削除しますか？')) return

    setError('')
    setSuccessMessage('')

    try {
      await projectApi.deleteProject(projectId)
      setProjects(projects.filter(p => p.id !== projectId))
      setSuccessMessage('プロジェクトが正常に削除されました')
      
      // 成功メッセージを3秒後に消去
      setTimeout(() => setSuccessMessage(''), 3000)
    } catch (err: any) {
      console.error('Failed to delete project:', err)
      setError(err.response?.data?.detail || 'プロジェクトの削除に失敗しました')
    }
  }

  const openChat = (projectId: string) => {
    router.push(`/chat/${projectId}`)
  }

  const filteredProjects = projects.filter(project =>
    project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (project.description?.toLowerCase().includes(searchQuery.toLowerCase()) ?? false)
  )

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container py-6">
        <h1 className="text-2xl font-bold text-gray-900">プロジェクト一覧</h1>
        <p className="text-gray-600 mt-1">作成済みのプロジェクトを管理します</p>

        <div className="mt-6">
          {error && (
            <div
              className="mb-4 bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded"
              aria-live="polite"
            >
              {error}
            </div>
          )}
          
          {successMessage && (
            <div
              className="mb-4 bg-green-50 border border-green-200 text-green-600 px-4 py-3 rounded"
              aria-live="polite"
            >
              {successMessage}
            </div>
          )}

          <div className="mb-6">
            <div className="flex flex-col sm:flex-row gap-4 mb-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="プロジェクトを検索..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9"
                />
              </div>
              <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                <DialogTrigger asChild>
                  <Button className="shrink-0">
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
          </div>

          {filteredProjects.length === 0 && projects.length > 0 ? (
            <Card>
              <CardContent className="py-8">
                <div className="text-center">
                  <h3 className="text-lg font-medium text-gray-900">検索結果が見つかりませんでした</h3>
                  <p className="text-gray-600 mt-2">
                    検索条件を変更してみてください
                  </p>
                </div>
              </CardContent>
            </Card>
          ) : projects.length === 0 ? (
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
              {filteredProjects.map((project) => (
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

export default function DashboardPage() {
  return (
    <AuthWrapper>
      <DashboardPageContent />
    </AuthWrapper>
  )
}