'use client'

import { useState, useEffect, useCallback } from 'react'
import { Upload, FileText, Trash2, AlertCircle, CheckCircle, Clock, RefreshCw, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Progress } from '@/components/ui/progress'
import { documentsApi, Document, UploadDocumentRequest, DocumentProcessingStatus } from '@/features/documents/api'

interface DocumentManagerProps {
  projectId: number
  className?: string
}

export default function DocumentManager({
  projectId,
  className = ''
}: DocumentManagerProps) {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const [dragActive, setDragActive] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({})
  const [processingStatus, setProcessingStatus] = useState<DocumentProcessingStatus[]>([])
  const [statusRefreshInterval, setStatusRefreshInterval] = useState<NodeJS.Timeout | null>(null)

  // ドキュメント一覧を取得
  const fetchDocuments = useCallback(async () => {
    if (!projectId) return

    setLoading(true)
    setError('')
    try {
      const response = await documentsApi.getDocumentsByProject(projectId)
      setDocuments(response.data || [])
    } catch (err: any) {
      console.error('Failed to fetch documents:', err)
      setError('ドキュメント一覧の取得に失敗しました')
      setDocuments([])
    } finally {
      setLoading(false)
    }
  }, [projectId])

  // 処理状況を取得
  const fetchProcessingStatus = useCallback(async () => {
    if (!projectId) return

    try {
      const response = await documentsApi.getProcessingStatus(projectId)
      setProcessingStatus(response.data || [])
      
      // 処理中のドキュメントがあるかチェック
      const hasUnprocessed = response.data?.some((status: DocumentProcessingStatus) => !status.processed)
      
      if (hasUnprocessed && !statusRefreshInterval) {
        // 5秒間隔で処理状況を更新
        const interval = setInterval(() => {
          fetchProcessingStatus()
        }, 5000)
        setStatusRefreshInterval(interval)
      } else if (!hasUnprocessed && statusRefreshInterval) {
        // 全ての処理が完了したら更新を停止
        clearInterval(statusRefreshInterval)
        setStatusRefreshInterval(null)
        fetchDocuments() // 最新のドキュメント情報を取得
      }
    } catch (err: any) {
      console.error('Failed to fetch processing status:', err)
    }
  }, [projectId, statusRefreshInterval, fetchDocuments])

  useEffect(() => {
    if (projectId) {
      fetchDocuments()
      fetchProcessingStatus()
    }
    
    // クリーンアップ
    return () => {
      if (statusRefreshInterval) {
        clearInterval(statusRefreshInterval)
      }
    }
  }, [projectId, fetchDocuments, fetchProcessingStatus])

  // ファイルアップロード処理
  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0 || !projectId) return

    setUploading(true)
    setError('')
    setUploadProgress({}) // 進行状況をリセット

    try {
      const uploadPromises = Array.from(files).map(async (file, index) => {
        const fileKey = `${file.name}_${index}`
        
        try {
          // ファイルサイズチェック（30MB制限）
          const maxSize = 30 * 1024 * 1024 // 30MB
          if (file.size > maxSize) {
            setUploadProgress(prev => ({ ...prev, [fileKey]: -1 })) // エラー状態
            throw new Error(`${file.name}: ファイルサイズが30MBを超えています`)
          }

          // 対応ファイル形式チェック
          const allowedTypes = ['.pdf', '.txt', '.md', '.docx', '.xlsx', '.xls', '.pptx']
          const fileExt = '.' + file.name.split('.').pop()?.toLowerCase()
          if (!allowedTypes.includes(fileExt)) {
            setUploadProgress(prev => ({ ...prev, [fileKey]: -1 })) // エラー状態
            throw new Error(`${file.name}: 対応していないファイル形式です (${allowedTypes.join(', ')})`)
          }

          // アップロード開始
          setUploadProgress(prev => ({ ...prev, [fileKey]: 0 }))

          const uploadData: UploadDocumentRequest = {
            project_id: projectId,
            file: file
          }

          // 模擬進行状況更新（実際のAPIが進行状況をサポートしていない場合）
          setUploadProgress(prev => ({ ...prev, [fileKey]: 50 }))
          
          const response = await documentsApi.uploadDocument(uploadData)
          
          // アップロード完了
          setUploadProgress(prev => ({ ...prev, [fileKey]: 100 }))
          
          return response
        } catch (error) {
          setUploadProgress(prev => ({ ...prev, [fileKey]: -1 })) // エラー状態
          throw error
        }
      })

      await Promise.all(uploadPromises)
      await fetchDocuments() // 一覧を再取得
      await fetchProcessingStatus() // 処理状況の監視を開始
      
      // 成功後、3秒後に進行状況をクリア
      setTimeout(() => {
        setUploadProgress({})
      }, 3000)
      
    } catch (err: any) {
      console.error('Failed to upload documents:', err)
      setError(err.message || 'ファイルのアップロードに失敗しました')
    } finally {
      setUploading(false)
    }
  }

  // ドラッグ&ドロップ処理
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files)
    }
  }, [handleFileUpload])

  // ドキュメント有効/無効切替
  const toggleDocumentActive = async (document: Document) => {
    try {
      await documentsApi.updateDocument(document.id, {
        is_active: !document.is_active
      })
      
      // ローカル状態を更新
      setDocuments(docs => 
        docs.map(doc => 
          doc.id === document.id 
            ? { ...doc, is_active: !doc.is_active }
            : doc
        )
      )
    } catch (err: any) {
      console.error('Failed to toggle document:', err)
      setError('ドキュメントの状態変更に失敗しました')
    }
  }

  // ドキュメント削除
  const deleteDocument = async (document: Document) => {
    if (!confirm(`「${document.original_filename}」を削除しますか？この操作は取り消せません。`)) {
      return
    }

    try {
      await documentsApi.deleteDocument(document.id)
      setDocuments(docs => docs.filter(doc => doc.id !== document.id))
    } catch (err: any) {
      console.error('Failed to delete document:', err)
      setError('ドキュメントの削除に失敗しました')
    }
  }

  // ファイルサイズを人間が読みやすい形式に変換
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  // 処理状況アイコン
  const getStatusIcon = (processed: boolean) => {
    if (processed) {
      return <CheckCircle className="h-4 w-4 text-green-500" />
    } else {
      return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
    }
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* ヘッダー */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-900">ドキュメント</h3>
        <Button
          onClick={() => document.getElementById('file-upload')?.click()}
          variant="outline"
          size="sm"
          disabled={uploading}
        >
          <Upload className="h-4 w-4 mr-2" />
          アップロード
        </Button>
      </div>

      {/* 隠しファイル入力 */}
      <input
        id="file-upload"
        type="file"
        multiple
        accept=".pdf,.txt,.md,.docx,.xlsx,.xls,.pptx"
        onChange={(e) => handleFileUpload(e.target.files)}
        className="hidden"
      />

      {/* エラー表示 */}
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-600 text-sm">{error}</p>
          <Button
            onClick={() => setError('')}
            variant="ghost"
            size="sm"
            className="mt-2 text-red-600 hover:text-red-700"
          >
            閉じる
          </Button>
        </div>
      )}

      {/* アップロード進行状況表示 */}
      {Object.keys(uploadProgress).length > 0 && (
        <div className="space-y-2 p-4 bg-gray-50 rounded-lg">
          <h4 className="text-sm font-medium text-gray-700 flex items-center">
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            アップロード進行状況
          </h4>
          {Object.entries(uploadProgress).map(([fileKey, progress]) => {
            const [filename] = fileKey.split('_')
            return (
              <div key={fileKey} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600 truncate">{filename}</span>
                  <span className={`text-sm font-medium ${
                    progress === -1 ? 'text-red-600' : 
                    progress === 100 ? 'text-green-600' : 'text-blue-600'
                  }`}>
                    {progress === -1 ? 'エラー' : 
                     progress === 100 ? '完了' : `${progress}%`}
                  </span>
                </div>
                <Progress 
                  value={progress === -1 ? 100 : progress} 
                  className={`h-2 ${progress === -1 ? '[&>div]:bg-red-500' : 
                    progress === 100 ? '[&>div]:bg-green-500' : '[&>div]:bg-blue-500'}`}
                />
              </div>
            )
          })}
        </div>
      )}

      {/* ベクトル化進行状況表示 (Task 25) */}
      {processingStatus.some(status => !status.processed) && (
        <div className="space-y-2 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h4 className="text-sm font-medium text-blue-800 flex items-center">
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ドキュメント処理状況
          </h4>
          <div className="space-y-2">
            {processingStatus
              .filter(status => !status.processed)
              .map((status) => (
                <div key={status.document_id} className="flex items-center justify-between text-sm">
                  <span className="text-blue-700 truncate flex items-center">
                    <Clock className="h-3 w-3 mr-1" />
                    {status.filename}
                  </span>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-blue-600">
                      {formatFileSize(status.file_size)}
                    </span>
                    <span className="text-xs text-blue-600">ベクトル化中...</span>
                  </div>
                </div>
              ))}
          </div>
          <p className="text-xs text-blue-600 mt-2">
            💡 ドキュメントが処理されるとRAG検索で活用されます
          </p>
        </div>
      )}

      {/* ドラッグ&ドロップエリア */}
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragActive
            ? 'border-blue-400 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        } ${uploading ? 'opacity-50 pointer-events-none' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => document.getElementById('file-upload')?.click()}
      >
        {uploading ? (
          <div className="flex items-center justify-center">
            <Loader2 className="h-6 w-6 animate-spin mr-2 text-blue-500" />
            <span className="text-sm text-gray-600">アップロード中...</span>
          </div>
        ) : (
          <>
            <Upload className="h-8 w-8 text-gray-400 mx-auto mb-3" />
            <p className="text-sm text-gray-600 mb-1">
              ファイルをドラッグ&ドロップ、またはクリックしてアップロード
            </p>
            <p className="text-xs text-gray-400">
              PDF, TXT, MD, DOCX, XLSX, XLS, PPTX (最大30MB)
            </p>
          </>
        )}
      </div>

      {/* ドキュメント一覧 */}
      <div className="space-y-2">
        {loading && (
          <div className="flex items-center justify-center py-4">
            <Loader2 className="h-5 w-5 animate-spin mr-2" />
            <span className="text-sm text-gray-600">読み込み中...</span>
          </div>
        )}

        {!loading && documents.length === 0 && (
          <div className="text-center py-6">
            <p className="text-sm text-gray-500">
              アップロードされたドキュメントはありません
            </p>
          </div>
        )}

        {!loading && documents.map((document) => (
          <div
            key={document.id}
            className={`flex items-center space-x-3 p-3 rounded-lg border transition-colors ${
              document.is_active
                ? 'bg-green-50 border-green-200'
                : 'bg-gray-50 border-gray-200'
            }`}
          >
            {/* ファイルアイコンと状態 */}
            <div className="flex-shrink-0">
              <div className="relative">
                <FileText className="h-6 w-6 text-gray-600" />
                <div className="absolute -top-1 -right-1">
                  {getStatusIcon(document.processed)}
                </div>
              </div>
            </div>

            {/* ドキュメント情報 */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {document.original_filename}
                </p>
                <div className="flex items-center space-x-2">
                  {/* 有効/無効スイッチ */}
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-gray-600">
                      {document.is_active ? '有効' : '無効'}
                    </span>
                    <Switch
                      checked={document.is_active}
                      onCheckedChange={() => toggleDocumentActive(document)}
                      size="sm"
                    />
                  </div>
                  
                  {/* 削除ボタン */}
                  <Button
                    onClick={() => deleteDocument(document)}
                    variant="ghost"
                    size="sm"
                    className="text-gray-400 hover:text-red-600"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              
              <div className="flex items-center space-x-4 mt-1">
                <span className="text-xs text-gray-500">
                  {formatFileSize(document.file_size)}
                </span>
                {document.chunks && document.chunks.length > 0 && (
                  <span className="text-xs text-gray-500">
                    {document.chunks.length} チャンク
                  </span>
                )}
                <span className="text-xs text-gray-500">
                  {new Date(document.created_at).toLocaleDateString('ja-JP')}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 一括操作 */}
      {documents.length > 0 && (
        <div className="flex items-center justify-between pt-4 border-t">
          <span className="text-xs text-gray-500">
            {documents.length} 件のドキュメント
            （有効: {documents.filter(d => d.is_active).length} 件）
          </span>
          <Button
            onClick={fetchDocuments}
            variant="ghost"
            size="sm"
            className="text-gray-600"
          >
            <RefreshCw className="h-4 w-4 mr-1" />
            更新
          </Button>
        </div>
      )}
    </div>
  )
}