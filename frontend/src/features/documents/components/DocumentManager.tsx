'use client'

import { useState, useEffect, useCallback } from 'react'
import { Upload, FileText, Trash2, AlertCircle, CheckCircle, Clock, RefreshCw, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { documentsApi, Document, UploadDocumentRequest } from '@/features/documents/api'

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

  useEffect(() => {
    if (projectId) {
      fetchDocuments()
    }
  }, [projectId, fetchDocuments])

  // ファイルアップロード処理
  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0 || !projectId) return

    setUploading(true)
    setError('')

    try {
      const uploadPromises = Array.from(files).map(async (file) => {
        // ファイルサイズチェック（30MB制限）
        const maxSize = 30 * 1024 * 1024 // 30MB
        if (file.size > maxSize) {
          throw new Error(`${file.name}: ファイルサイズが30MBを超えています`)
        }

        // 対応ファイル形式チェック
        const allowedTypes = ['.pdf', '.txt', '.md', '.docx']
        const fileExt = '.' + file.name.split('.').pop()?.toLowerCase()
        if (!allowedTypes.includes(fileExt)) {
          throw new Error(`${file.name}: 対応していないファイル形式です (${allowedTypes.join(', ')})`)
        }

        const uploadData: UploadDocumentRequest = {
          project_id: projectId,
          file: file
        }

        return await documentsApi.uploadDocument(uploadData)
      })

      await Promise.all(uploadPromises)
      await fetchDocuments() // 一覧を再取得
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
      await documentsApi.updateDocument(parseInt(document.id), {
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
    if (!confirm(`「${document.filename}」を削除しますか？この操作は取り消せません。`)) {
      return
    }

    try {
      await documentsApi.deleteDocument(parseInt(document.id))
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
  const getStatusIcon = (status: Document['processing_status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'processing':
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-500" />
      default:
        return <Clock className="h-4 w-4 text-gray-400" />
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
        accept=".pdf,.txt,.md,.docx"
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
              PDF, TXT, MD, DOCX (最大30MB)
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
                  {getStatusIcon(document.processing_status)}
                </div>
              </div>
            </div>

            {/* ドキュメント情報 */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {document.filename}
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
                {document.chunk_count && (
                  <span className="text-xs text-gray-500">
                    {document.chunk_count} チャンク
                  </span>
                )}
                <span className="text-xs text-gray-500">
                  {new Date(document.upload_date).toLocaleDateString('ja-JP')}
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