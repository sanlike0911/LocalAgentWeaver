'use client'

import { useState, useEffect, useCallback } from 'react'
import { ChevronDown, Download, Trash2, AlertCircle, CheckCircle, Clock, Loader2, X } from 'lucide-react'
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

interface ModelPreset {
  name: string
  display_name: string
  description: string
  category: string
  tags: string[]
  recommended: boolean
  size_estimate: string
}

interface ModelCategory {
  name: string
  description: string
}

interface ModelPresetsResponse {
  provider: string
  models: ModelPreset[]
  categories: Record<string, ModelCategory>
  metadata: any
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
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
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
  const [modelPresets, setModelPresets] = useState<ModelPresetsResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [showModelDialog, setShowModelDialog] = useState(false)
  const [error, setError] = useState('')
  const [installTasks, setInstallTasks] = useState<InstallTask[]>([])
  const [refreshInterval, setRefreshInterval] = useState<NodeJS.Timeout | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<string>('all')

  // プリセットモデルを取得
  const fetchModelPresets = async () => {
    try {
      const response = await chatApi.getModelPresets(provider, {
        category: selectedCategory === 'all' ? undefined : selectedCategory
      })
      setModelPresets(response.data)
    } catch (err: any) {
      console.error('Failed to fetch model presets:', err)
      setError('モデルプリセットの取得に失敗しました')
    }
  }

  // モデル一覧を取得
  const fetchModels = useCallback(async () => {
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
  }, [provider])

  // インストール進行状況を監視
  const monitorInstallProgress = useCallback(async () => {
    // 最新の状態を参照するために関数型の更新を使用
    setInstallTasks(currentTasks => {
      const runningTasks = currentTasks.filter(task => 
        task.status === 'pending' || task.status === 'running'
      )

      if (runningTasks.length === 0) {
        return currentTasks
      }

      // 非同期でタスクの進捗を取得して更新
      Promise.allSettled(
        runningTasks.map(task => chatApi.getInstallStatus(task.task_id))
      ).then(results => {
        setInstallTasks(latestTasks => {
          let hasCompletedTasks = false
          
          const updatedTasks = latestTasks.map(task => {
            const resultIndex = runningTasks.findIndex(t => t.task_id === task.task_id)
            if (resultIndex >= 0) {
              const result = results[resultIndex]
              if (result.status === 'fulfilled') {
                const newTask = result.value.data
                
                // 完了状態の変化を検出
                if (newTask.status === 'completed' && task.status !== 'completed') {
                  hasCompletedTasks = true
                }
                
                return newTask
              }
            }
            return task
          })

          // 完了したタスクがあればモデル一覧を更新
          if (hasCompletedTasks) {
            fetchModels()
          }

          return updatedTasks
        })
      }).catch(err => {
        console.error('Failed to monitor install progress:', err)
      })

      return currentTasks // 非同期処理開始時点では現在の状態を返す
    })
  }, [fetchModels])

  useEffect(() => {
    if (showModelDialog) {
      fetchModels()
      fetchModelPresets()
    } else {
      // ダイアログが閉じられたら、完了・キャンセル・失敗したタスクをクリア
      setInstallTasks(prev => 
        prev.filter(task => 
          task.status === 'pending' || task.status === 'running'
        )
      )
    }
  }, [showModelDialog, provider])

  useEffect(() => {
    if (showModelDialog && modelPresets) {
      fetchModelPresets()
    }
  }, [selectedCategory])

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
  }, [installTasks, refreshInterval, monitorInstallProgress])

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

  // インストールをキャンセル
  const cancelInstallTask = async (taskId: string) => {
    try {
      await chatApi.cancelInstallTask(taskId)
      
      // タスクリストから該当タスクを更新
      setInstallTasks(prev => 
        prev.map(task => 
          task.task_id === taskId 
            ? { ...task, status: 'cancelled' as const, message: 'インストールがキャンセルされました' }
            : task
        )
      )
    } catch (err: any) {
      console.error('Failed to cancel install task:', err)
      setError('インストールのキャンセルに失敗しました')
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
      case 'cancelled':
        return <X className="h-4 w-4 text-gray-500" />
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

            {/* カテゴリフィルター */}
            {modelPresets && Object.keys(modelPresets.categories).length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-3">カテゴリ</h3>
                <div className="flex flex-wrap gap-2 mb-4">
                  <button
                    onClick={() => setSelectedCategory('all')}
                    className={`px-3 py-1 text-xs rounded-full border transition-colors ${
                      selectedCategory === 'all'
                        ? 'bg-blue-100 text-blue-800 border-blue-300'
                        : 'bg-gray-100 text-gray-600 border-gray-300 hover:bg-gray-200'
                    }`}
                  >
                    すべて
                  </button>
                  {Object.entries(modelPresets.categories).map(([key, category]) => (
                    <button
                      key={key}
                      onClick={() => setSelectedCategory(key)}
                      className={`px-3 py-1 text-xs rounded-full border transition-colors ${
                        selectedCategory === key
                          ? 'bg-blue-100 text-blue-800 border-blue-300'
                          : 'bg-gray-100 text-gray-600 border-gray-300 hover:bg-gray-200'
                      }`}
                      title={category.description}
                    >
                      {category.name}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* プリセットモデル（インストール可能） */}
            {modelPresets && (
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-3">
                  {selectedCategory === 'all' ? '利用可能モデル' : modelPresets.categories[selectedCategory]?.name || '利用可能モデル'}
                </h3>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {modelPresets.models.map((model) => {
                    const installTask = getModelInstallTask(model.name)
                    const isInstalled = isModelInstalled(model.name)
                    
                    return (
                      <div
                        key={model.name}
                        className="flex items-center justify-between p-3 border rounded-lg"
                      >
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-1">
                            <p className="text-sm font-medium">{model.display_name}</p>
                            {model.recommended && (
                              <span className="px-2 py-0.5 bg-green-100 text-green-800 text-xs rounded">
                                推奨
                              </span>
                            )}
                          </div>
                          <p className="text-xs text-gray-500 mb-1">{model.description}</p>
                          <div className="flex items-center space-x-2">
                            <span className="text-xs text-gray-400">{model.size_estimate}</span>
                            <div className="flex flex-wrap gap-1">
                              {model.tags.slice(0, 2).map((tag) => (
                                <span key={tag} className="px-1.5 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">
                                  {tag}
                                </span>
                              ))}
                            </div>
                          </div>
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
                              {(installTask.status === 'pending' || installTask.status === 'running') && (
                                <Button
                                  onClick={() => cancelInstallTask(installTask.task_id)}
                                  variant="ghost"
                                  size="sm"
                                  className="text-gray-400 hover:text-red-600"
                                >
                                  <X className="h-4 w-4" />
                                </Button>
                              )}
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
            )}

            {/* インストール進行状況 */}
            {installTasks.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-3">インストール状況</h3>
                <div className="space-y-2 max-h-32 overflow-y-auto">
                  {installTasks.map((task) => (
                    <div key={task.task_id} className="p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium">{task.model_name}</span>
                        <div className="flex items-center space-x-2">
                          {getStatusIcon(task)}
                          {(task.status === 'pending' || task.status === 'running') && (
                            <Button
                              onClick={() => cancelInstallTask(task.task_id)}
                              variant="ghost"
                              size="sm"
                              className="text-gray-400 hover:text-red-600"
                            >
                              <X className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
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

                      {task.status === 'cancelled' && (
                        <p className="text-xs text-gray-600">{task.message}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="flex justify-between pt-4 border-t">
            <div className="flex space-x-2">
              <Button
                onClick={() => {
                  fetchModels()
                  fetchModelPresets()
                }}
                variant="outline"
                disabled={loading}
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                ) : null}
                更新
              </Button>
            </div>
            <Button onClick={() => setShowModelDialog(false)}>
              閉じる
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}