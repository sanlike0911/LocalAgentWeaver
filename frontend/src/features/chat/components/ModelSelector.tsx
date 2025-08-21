'use client'

import { useState, useEffect } from 'react'
import { ChevronDown, Download, Trash2, AlertCircle, CheckCircle, Clock, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Progress } from '@/components/ui/progress'
import { chatApi } from '@/utils/api'

interface Model {
  name: string
  size?: string
  modified?: string
  digest?: string
  details?: any
}

interface ModelSelectorProps {
  provider: 'ollama' | 'lm_studio'
  selectedModel: string
  onModelSelect: (model: string) => void
  className?: string
}

interface InstallTask {
  task_id: string
  model_name: string
  provider: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  message: string
  created_at: string
  updated_at: string
}

export default function ModelSelector({
  provider,
  selectedModel,
  onModelSelect,
  className = ''
}: ModelSelectorProps) {
  const [availableModels, setAvailableModels] = useState<Model[]>([])
  const [loading, setLoading] = useState(false)
  const [showModelDialog, setShowModelDialog] = useState(false)
  const [error, setError] = useState('')
  const [installTasks, setInstallTasks] = useState<InstallTask[]>([])
  const [refreshInterval, setRefreshInterval] = useState<NodeJS.Timeout | null>(null)

  // よく使われるモデルのプリセット
  const popularModels = {
    ollama: [
      { name: 'llama3', description: 'Meta の Llama 3 モデル' },
      { name: 'codellama', description: 'コード生成特化モデル' },
      { name: 'mistral', description: 'Mistral AI の高性能モデル' },
      { name: 'gemma', description: 'Google の軽量モデル' },
      { name: 'qwen', description: 'Alibaba の多言語モデル' }
    ],
    lm_studio: [
      { name: 'llama-3-8b-instruct', description: 'Meta Llama 3 8B' },
      { name: 'codellama-7b', description: 'Code Llama 7B' },
      { name: 'mistral-7b-instruct', description: 'Mistral 7B Instruct' }
    ]
  }

  // モデル一覧を取得
  const fetchModels = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await chatApi.getModels(provider)
      setAvailableModels(response.data.models || [])
    } catch (err: any) {
      console.error('Failed to fetch models:', err)
      setError('モデル一覧の取得に失敗しました')
      setAvailableModels([])
    } finally {
      setLoading(false)
    }
  }

  // インストール進行状況を監視
  const monitorInstallProgress = async () => {
    const runningTasks = installTasks.filter(task => 
      task.status === 'pending' || task.status === 'running'
    )

    if (runningTasks.length === 0) {
      if (refreshInterval) {
        clearInterval(refreshInterval)
        setRefreshInterval(null)
      }
      return
    }

    try {
      const taskPromises = runningTasks.map(task =>
        chatApi.getInstallStatus(task.task_id)
      )
      
      const results = await Promise.allSettled(taskPromises)
      
      const updatedTasks = installTasks.map(task => {
        const resultIndex = runningTasks.findIndex(t => t.task_id === task.task_id)
        if (resultIndex >= 0) {
          const result = results[resultIndex]
          if (result.status === 'fulfilled') {
            return result.value.data
          }
        }
        return task
      })

      setInstallTasks(updatedTasks)

      // 完了したタスクがあればモデル一覧を更新
      const completedTasks = updatedTasks.filter(task => 
        task.status === 'completed' && 
        !installTasks.find(t => t.task_id === task.task_id && t.status === 'completed')
      )
      
      if (completedTasks.length > 0) {
        await fetchModels()
      }
    } catch (err) {
      console.error('Failed to monitor install progress:', err)
    }
  }

  useEffect(() => {
    if (showModelDialog) {
      fetchModels()
    }
  }, [showModelDialog, provider])

  useEffect(() => {
    const hasRunningTasks = installTasks.some(task => 
      task.status === 'pending' || task.status === 'running'
    )

    if (hasRunningTasks && !refreshInterval) {
      const interval = setInterval(monitorInstallProgress, 2000)
      setRefreshInterval(interval)
    } else if (!hasRunningTasks && refreshInterval) {
      clearInterval(refreshInterval)
      setRefreshInterval(null)
    }

    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval)
      }
    }
  }, [installTasks])

  // モデルをインストール
  const installModel = async (modelName: string) => {
    try {
      const response = await chatApi.installModel({
        model_name: modelName,
        provider: provider
      })
      
      const newTask: InstallTask = {
        task_id: response.data.task_id,
        model_name: modelName,
        provider: provider,
        status: 'pending',
        progress: 0,
        message: 'インストール開始...',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }
      
      setInstallTasks(prev => [...prev, newTask])
    } catch (err: any) {
      console.error('Failed to install model:', err)
      setError(`${modelName}のインストールに失敗しました`)
    }
  }

  // モデルを削除
  const deleteModel = async (modelName: string) => {
    if (!confirm(`${modelName}を削除しますか？この操作は取り消せません。`)) {
      return
    }

    try {
      await chatApi.deleteModel(modelName, provider)
      await fetchModels()
    } catch (err: any) {
      console.error('Failed to delete model:', err)
      setError(`${modelName}の削除に失敗しました`)
    }
  }

  const isModelInstalled = (modelName: string) => {
    return availableModels.some(model => model.name === modelName)
  }

  const getModelInstallTask = (modelName: string) => {
    return installTasks.find(task => 
      task.model_name === modelName && 
      (task.status === 'pending' || task.status === 'running')
    )
  }

  const getStatusIcon = (task: InstallTask) => {
    switch (task.status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'running':
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-500" />
      default:
        return <Clock className="h-4 w-4 text-gray-400" />
    }
  }

  return (
    <>
      <div className={`flex items-center space-x-2 ${className}`}>
        <label className="text-sm font-medium">Model:</label>
        <div className="relative">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowModelDialog(true)}
            className="justify-between min-w-[120px]"
          >
            <span className="truncate">{selectedModel}</span>
            <ChevronDown className="h-4 w-4 ml-2" />
          </Button>
          
          {/* インストール進行中の表示 */}
          {getModelInstallTask(selectedModel) && (
            <div className="absolute -top-1 -right-1">
              <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
            </div>
          )}
        </div>
      </div>

      <Dialog open={showModelDialog} onOpenChange={setShowModelDialog}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle>
              {provider === 'ollama' ? 'Ollama' : 'LM Studio'} モデル選択
            </DialogTitle>
          </DialogHeader>

          <div className="flex flex-col space-y-4 flex-1 overflow-hidden">
            {/* エラー表示 */}
            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-600 text-sm">{error}</p>
              </div>
            )}

            {/* インストール済みモデル */}
            <div>
              <h3 className="text-sm font-medium text-gray-900 mb-3">インストール済みモデル</h3>
              <div className="space-y-2 max-h-32 overflow-y-auto">
                {loading ? (
                  <div className="flex items-center justify-center py-4">
                    <Loader2 className="h-5 w-5 animate-spin mr-2" />
                    <span className="text-sm text-gray-600">読み込み中...</span>
                  </div>
                ) : availableModels.length === 0 ? (
                  <p className="text-sm text-gray-500 text-center py-4">
                    インストール済みモデルがありません
                  </p>
                ) : (
                  availableModels.map((model) => (
                    <div
                      key={model.name}
                      className={`flex items-center justify-between p-3 border rounded-lg cursor-pointer transition-colors ${
                        selectedModel === model.name
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:bg-gray-50'
                      }`}
                      onClick={() => {
                        onModelSelect(model.name)
                        setShowModelDialog(false)
                      }}
                    >
                      <div className="flex-1">
                        <p className="text-sm font-medium">{model.name}</p>
                        {model.size && (
                          <p className="text-xs text-gray-500">{model.size}</p>
                        )}
                      </div>
                      
                      {selectedModel === model.name && (
                        <CheckCircle className="h-4 w-4 text-blue-500" />
                      )}
                      
                      <Button
                        onClick={(e) => {
                          e.stopPropagation()
                          deleteModel(model.name)
                        }}
                        variant="ghost"
                        size="sm"
                        className="ml-2 text-gray-400 hover:text-red-600"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* 人気モデル（インストール可能） */}
            <div>
              <h3 className="text-sm font-medium text-gray-900 mb-3">推奨モデル</h3>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {popularModels[provider].map((model) => {
                  const installTask = getModelInstallTask(model.name)
                  const isInstalled = isModelInstalled(model.name)
                  
                  return (
                    <div
                      key={model.name}
                      className="flex items-center justify-between p-3 border rounded-lg"
                    >
                      <div className="flex-1">
                        <p className="text-sm font-medium">{model.name}</p>
                        <p className="text-xs text-gray-500">{model.description}</p>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        {installTask ? (
                          <div className="flex items-center space-x-2">
                            {getStatusIcon(installTask)}
                            <div className="w-24">
                              <Progress 
                                value={installTask.progress * 100} 
                                className="h-2"
                              />
                            </div>
                            <span className="text-xs text-gray-600">
                              {Math.round(installTask.progress * 100)}%
                            </span>
                          </div>
                        ) : isInstalled ? (
                          <Button
                            onClick={() => {
                              onModelSelect(model.name)
                              setShowModelDialog(false)
                            }}
                            variant="outline"
                            size="sm"
                          >
                            選択
                          </Button>
                        ) : (
                          <Button
                            onClick={() => installModel(model.name)}
                            variant="outline"
                            size="sm"
                          >
                            <Download className="h-4 w-4 mr-1" />
                            インストール
                          </Button>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* インストール進行状況 */}
            {installTasks.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-3">インストール状況</h3>
                <div className="space-y-2 max-h-32 overflow-y-auto">
                  {installTasks.map((task) => (
                    <div key={task.task_id} className="p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium">{task.model_name}</span>
                        {getStatusIcon(task)}
                      </div>
                      
                      {(task.status === 'pending' || task.status === 'running') && (
                        <div className="space-y-1">
                          <Progress value={task.progress * 100} className="h-2" />
                          <p className="text-xs text-gray-600">{task.message}</p>
                        </div>
                      )}
                      
                      {task.status === 'failed' && (
                        <p className="text-xs text-red-600">{task.message}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="flex justify-between pt-4 border-t">
            <Button
              onClick={fetchModels}
              variant="outline"
              disabled={loading}
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : null}
              更新
            </Button>
            <Button onClick={() => setShowModelDialog(false)}>
              閉じる
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}