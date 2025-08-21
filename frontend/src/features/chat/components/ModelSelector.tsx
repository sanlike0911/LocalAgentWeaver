'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle,
  DialogDescription 
} from '@/components/ui/dialog'
import { Progress } from '@/components/ui/progress'
import { Download, Check, X, Loader2 } from 'lucide-react'

interface Model {
  name: string
  size?: string
  description?: string
  installed: boolean
}

interface ModelSelectorProps {
  provider: 'ollama' | 'lm_studio'
  selectedModel: string
  onModelSelect: (model: string) => void
  onModelInstall?: (model: string) => Promise<void>
}

export default function ModelSelector({ 
  provider, 
  selectedModel, 
  onModelSelect,
  onModelInstall 
}: ModelSelectorProps) {
  const [models, setModels] = useState<Model[]>([])
  const [loading, setLoading] = useState(false)
  const [showInstallDialog, setShowInstallDialog] = useState(false)
  const [installProgress, setInstallProgress] = useState<{
    model: string
    progress: number
    status: string
    message: string
    taskId?: string
  } | null>(null)

  useEffect(() => {
    fetchModels()
  }, [provider])

  const fetchModels = async () => {
    try {
      setLoading(true)
      const response = await fetch(`/api/chat/models?provider=${provider}`)
      const data = await response.json()
      
      // Combine installed and available models
      const allModels: Model[] = [
        ...data.installed.map((model: any) => ({ ...model, installed: true })),
        ...data.available.map((model: any) => ({ ...model, installed: false }))
      ]
      
      setModels(allModels)
    } catch (error) {
      console.error('Failed to fetch models:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleModelSelect = (modelName: string) => {
    const model = models.find(m => m.name === modelName)
    
    if (!model?.installed) {
      // Show install confirmation dialog
      setInstallProgress({
        model: modelName,
        progress: 0,
        status: 'pending',
        message: 'インストールを開始しますか？'
      })
      setShowInstallDialog(true)
    } else {
      onModelSelect(modelName)
    }
  }

  const startModelInstall = async () => {
    if (!installProgress) return

    try {
      setInstallProgress(prev => prev ? { 
        ...prev, 
        status: 'starting', 
        message: 'インストールを開始しています...' 
      } : null)

      const response = await fetch('/api/chat/models/install', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model_name: installProgress.model,
          provider: provider
        })
      })

      const result = await response.json()
      
      if (result.task_id) {
        setInstallProgress(prev => prev ? { 
          ...prev, 
          taskId: result.task_id,
          status: 'downloading',
          message: 'ダウンロード中...' 
        } : null)
        
        // Start polling for progress
        pollInstallProgress(result.task_id)
      }
    } catch (error) {
      console.error('Failed to start model install:', error)
      setInstallProgress(prev => prev ? { 
        ...prev, 
        status: 'error',
        message: 'インストールの開始に失敗しました' 
      } : null)
    }
  }

  const pollInstallProgress = async (taskId: string) => {
    const poll = async () => {
      try {
        const response = await fetch(`/api/chat/models/install/${taskId}`)
        const progress = await response.json()
        
        setInstallProgress(prev => prev ? {
          ...prev,
          progress: progress.progress || 0,
          status: progress.status,
          message: progress.message || 'インストール中...'
        } : null)

        if (progress.status === 'completed') {
          setInstallProgress(prev => prev ? {
            ...prev,
            progress: 100,
            message: 'インストール完了！'
          } : null)
          
          // Refresh models list and close dialog
          setTimeout(() => {
            fetchModels()
            setShowInstallDialog(false)
            if (installProgress) {
              onModelSelect(installProgress.model)
            }
          }, 1500)
        } else if (progress.status === 'failed') {
          setInstallProgress(prev => prev ? {
            ...prev,
            status: 'error',
            message: progress.message || 'インストールに失敗しました'
          } : null)
        } else {
          // Continue polling
          setTimeout(poll, 2000)
        }
      } catch (error) {
        console.error('Failed to poll install progress:', error)
        setInstallProgress(prev => prev ? {
          ...prev,
          status: 'error',
          message: '進行状況の取得に失敗しました'
        } : null)
      }
    }
    
    poll()
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center space-x-2">
        <Input 
          value={selectedModel}
          onChange={(e) => onModelSelect(e.target.value)}
          placeholder="モデル名を入力"
          className="flex-1"
        />
        <Button 
          variant="outline" 
          size="sm"
          onClick={fetchModels}
          disabled={loading}
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : '更新'}
        </Button>
      </div>

      {models.length > 0 && (
        <div className="max-h-40 overflow-y-auto border rounded p-2 space-y-1">
          {models.map((model) => (
            <div 
              key={model.name}
              className={`flex items-center justify-between p-2 rounded cursor-pointer hover:bg-gray-100 ${
                selectedModel === model.name ? 'bg-blue-50 border border-blue-200' : ''
              }`}
              onClick={() => handleModelSelect(model.name)}
            >
              <div className="flex-1">
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium">{model.name}</span>
                  {model.installed ? (
                    <Check className="h-4 w-4 text-green-600" />
                  ) : (
                    <Download className="h-4 w-4 text-gray-400" />
                  )}
                </div>
                {model.size && (
                  <span className="text-xs text-gray-500">{model.size}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Install Progress Dialog */}
      <Dialog open={showInstallDialog} onOpenChange={setShowInstallDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>モデルのインストール</DialogTitle>
            <DialogDescription>
              {installProgress?.model} をインストールします
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="text-sm text-gray-600">
              {installProgress?.message}
            </div>
            
            {installProgress?.status === 'downloading' && (
              <Progress value={installProgress.progress} className="w-full" />
            )}
            
            <div className="flex justify-end space-x-2">
              {installProgress?.status === 'pending' && (
                <>
                  <Button 
                    variant="outline" 
                    onClick={() => setShowInstallDialog(false)}
                  >
                    キャンセル
                  </Button>
                  <Button onClick={startModelInstall}>
                    インストール開始
                  </Button>
                </>
              )}
              
              {installProgress?.status === 'error' && (
                <Button 
                  variant="outline" 
                  onClick={() => setShowInstallDialog(false)}
                >
                  閉じる
                </Button>
              )}
              
              {installProgress?.status === 'completed' && (
                <Button 
                  onClick={() => setShowInstallDialog(false)}
                  className="bg-green-600 hover:bg-green-700"
                >
                  完了
                </Button>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}