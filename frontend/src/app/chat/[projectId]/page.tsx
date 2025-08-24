'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { useParams } from 'next/navigation'
import { Send, ArrowLeft, Bot, User, Settings, Users } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { projectApi, chatApi, Project } from '@/utils/api'
import { Team, Agent } from '@/features/teams/api'
import TeamSelectorModal from '@/features/teams/components/TeamSelectorModal'
import TeamEditorModal from '@/features/teams/components/TeamEditorModal'
import DocumentManager from '@/features/documents/components/DocumentManager'
import ModelSelector from '@/features/chat/components/ModelSelector'
import AuthWrapper from '@/components/AuthWrapper'
import { formatResponseTime } from '@/utils/timeFormat'

interface Message {
  id: string
  content: string
  sender: 'user' | 'assistant'
  timestamp: Date
  responseTime?: number // ミリ秒単位の応答時間（アシスタントメッセージのみ）
}

// Document interface is now in DocumentManager
// Team and Agent interfaces are now imported from @/features/teams/api

function ChatPageContent() {
  const [project, setProject] = useState<Project | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [llmProvider, setLlmProvider] = useState<'ollama' | 'lm_studio'>('ollama')
  const [selectedModel, setSelectedModel] = useState('llama3.2:1b')
  const [llmHealthStatus, setLlmHealthStatus] = useState<any>(null)
  
  // Document management state - now handled by DocumentManager component
  
  // Team management state
  const [selectedTeam, setSelectedTeam] = useState<Team | null>(null)
  const [showTeamSelector, setShowTeamSelector] = useState(false)
  const [showTeamEditor, setShowTeamEditor] = useState(false)
  const [editingTeam, setEditingTeam] = useState<Team | null>(null)
  const [teamEditorMode, setTeamEditorMode] = useState<'create' | 'edit'>('create')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const router = useRouter()
  const params = useParams()
  const projectId = params.projectId as string

  useEffect(() => {
    fetchProject()
    checkLLMHealth()
  }, [projectId])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const fetchProject = async () => {
    try {
      const response = await projectApi.getProject(projectId)
      setProject(response.data)
    } catch (err) {
      setError('プロジェクトの取得に失敗しました')
      router.push('/dashboard')
    }
  }

  const checkLLMHealth = async () => {
    try {
      const response = await chatApi.checkLLMHealth()
      setLlmHealthStatus(response.data)
    } catch (err) {
      console.error('Failed to check LLM health:', err)
      setLlmHealthStatus({
        ollama: { status: 'error', message: 'ヘルスチェックに失敗しました' },
        lm_studio: { status: 'error', message: 'ヘルスチェックに失敗しました' }
      })
    }
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  // Document management functions are now handled by DocumentManager component

  // Team management functions
  const handleSelectTeam = (team: Team) => {
    setSelectedTeam(team)
    setShowTeamSelector(false)
  }

  const handleEditTeam = (team: Team) => {
    setEditingTeam(team)
    setTeamEditorMode('edit')
    setShowTeamSelector(false)
    setShowTeamEditor(true)
  }

  const handleCreateTeam = () => {
    setEditingTeam(null)
    setTeamEditorMode('create')
    setShowTeamSelector(false)
    setShowTeamEditor(true)
  }

  const handleSaveTeam = (team: Team) => {
    // TODO: API call to save team
    console.log('Saving team:', team)
    if (teamEditorMode === 'create' || team.id === selectedTeam?.id) {
      setSelectedTeam(team)
    }
    setShowTeamEditor(false)
  }

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputMessage.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputMessage.trim(),
      sender: 'user',
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)

    // 応答時間測定開始
    const startTime = Date.now()

    try {
      const response = await chatApi.sendMessage({
        project_id: projectId,
        message: userMessage.content,
        provider: llmProvider,
        model: selectedModel
      })
      
      // 応答時間計算
      const endTime = Date.now()
      const responseTime = endTime - startTime
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response.data.message,
        sender: 'assistant',
        timestamp: new Date(),
        responseTime
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (err: any) {
      setError(err.response?.data?.detail || 'メッセージの送信に失敗しました')
      
      // エラー時も応答時間を記録
      const endTime = Date.now()
      const responseTime = endTime - startTime
      
      // フォールバック応答
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: `申し訳ございません。LLMサーバーに接続できませんでした。Ollama/LM Studioが起動していることを確認してください。`,
        sender: 'assistant',
        timestamp: new Date(),
        responseTime
      }
      setMessages(prev => [...prev, assistantMessage])
    } finally {
      setIsLoading(false)
    }
  }

  if (!project) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center py-4">
            <Button
              variant="ghost"
              onClick={() => router.push('/dashboard')}
              className="mr-4"
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">{project.name}</h1>
              {project.description && (
                <p className="text-gray-600 text-sm">{project.description}</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 3 Column Layout */}
      <div className="flex h-[calc(100vh-80px)]">
        {/* Left Sidebar - Documents and Team */}
        <div className="w-80 bg-white shadow-sm border-r overflow-y-auto">
          {/* Team Selection Area */}
          <div className="p-4 border-b">
            <div 
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100 transition-colors"
              onClick={() => setShowTeamSelector(true)}
            >
              <div className="flex items-center">
                <Users className="h-5 w-5 text-gray-600 mr-2" />
                <div>
                  <p className="font-medium text-sm">
                    {selectedTeam?.name || 'チームを選択'}
                  </p>
                  {selectedTeam?.description && (
                    <p className="text-xs text-gray-500 truncate">
                      {selectedTeam.description}
                    </p>
                  )}
                </div>
              </div>
              <Settings className="h-4 w-4 text-gray-400" />
            </div>
          </div>

          {/* Document Management */}
          <div className="p-4">
            <DocumentManager projectId={parseInt(projectId)} />
          </div>
        </div>

        {/* Center - Chat Area */}
        <div className="flex-1 flex flex-col">
          {error && (
            <div className="m-4 bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded">
              {error}
            </div>
          )}

          <Card className="flex-1 m-4 flex flex-col">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center">
                  <Bot className="mr-2 h-5 w-5" />
                  AIアシスタント
                </div>
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2">
                    <label className="text-sm font-medium">Provider:</label>
                    <div className="relative">
                      <select 
                        value={llmProvider}
                        onChange={(e) => {
                          setLlmProvider(e.target.value as 'ollama' | 'lm_studio')
                          checkLLMHealth()
                        }}
                        className="text-sm border rounded px-2 py-1 pr-8"
                      >
                        <option value="ollama">Ollama</option>
                        <option value="lm_studio">LM Studio</option>
                      </select>
                      {llmHealthStatus && (
                        <div className={`absolute right-1 top-1/2 transform -translate-y-1/2 w-2 h-2 rounded-full ${
                          llmHealthStatus[llmProvider]?.status === 'healthy' 
                            ? 'bg-green-500' 
                            : llmHealthStatus[llmProvider]?.status === 'unreachable'
                            ? 'bg-red-500'
                            : 'bg-yellow-500'
                        }`} title={llmHealthStatus[llmProvider]?.message || ''} />
                      )}
                    </div>
                  </div>
                  <ModelSelector
                    provider={llmProvider}
                    selectedModel={selectedModel}
                    onModelSelect={setSelectedModel}
                  />
                </div>
              </CardTitle>
            </CardHeader>
            
            <CardContent className="flex-1 flex flex-col">
              <div className="flex-1 overflow-y-auto mb-4 space-y-4">
                {messages.length === 0 ? (
                  <div className="text-center py-8">
                    <Bot className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                    <p className="text-gray-600">
                      こんにちは！何かお手伝いできることはありますか？
                    </p>
                  </div>
                ) : (
                  messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex items-start space-x-2 ${
                        message.sender === 'user' ? 'justify-end' : 'justify-start'
                      }`}
                    >
                      {message.sender === 'assistant' && (
                        <div className="flex-shrink-0">
                          <Bot className="h-6 w-6 text-blue-600" />
                        </div>
                      )}
                      <div
                        className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                          message.sender === 'user'
                            ? 'bg-primary text-primary-foreground'
                            : 'bg-gray-100 text-gray-900'
                        }`}
                      >
                        <p className="text-sm">{message.content}</p>
                        <div className={`text-xs mt-1 ${
                          message.sender === 'user' 
                            ? 'text-primary-foreground/70' 
                            : 'text-gray-500'
                        }`}>
                          <p>
                            {message.timestamp.toLocaleTimeString('ja-JP', { 
                              hour: '2-digit', 
                              minute: '2-digit' 
                            })}
                          </p>
                          {message.sender === 'assistant' && message.responseTime && (
                            <p className="mt-0.5 text-xs">
                              {formatResponseTime(message.responseTime)}
                            </p>
                          )}
                        </div>
                      </div>
                      {message.sender === 'user' && (
                        <div className="flex-shrink-0">
                          <User className="h-6 w-6 text-green-600" />
                        </div>
                      )}
                    </div>
                  ))
                )}
                {isLoading && (
                  <div className="flex items-start space-x-2">
                    <Bot className="h-6 w-6 text-blue-600" />
                    <div className="bg-gray-100 px-4 py-2 rounded-lg">
                      <div className="flex space-x-1">
                        <div className="animate-bounce delay-0 h-2 w-2 bg-gray-500 rounded-full"></div>
                        <div className="animate-bounce delay-100 h-2 w-2 bg-gray-500 rounded-full"></div>
                        <div className="animate-bounce delay-200 h-2 w-2 bg-gray-500 rounded-full"></div>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              <form onSubmit={sendMessage} className="flex space-x-2">
                <Input
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder="メッセージを入力してください..."
                  disabled={isLoading}
                  className="flex-1"
                />
                <Button type="submit" disabled={!inputMessage.trim() || isLoading}>
                  <Send className="h-4 w-4" />
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>

        {/* Right Sidebar - Citations/References and LLM Status */}
        <div className="w-64 bg-white shadow-sm border-l overflow-y-auto">
          <div className="p-4 border-b">
            <h3 className="text-sm font-medium text-gray-900 mb-3">LLM接続状態</h3>
            {llmHealthStatus ? (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-600">
                    {llmProvider === 'ollama' ? 'Ollama' : 'LM Studio'}:
                  </span>
                  <div className="flex items-center space-x-1">
                    <div className={`w-2 h-2 rounded-full ${
                      llmHealthStatus[llmProvider]?.status === 'healthy' 
                        ? 'bg-green-500' 
                        : llmHealthStatus[llmProvider]?.status === 'unreachable'
                        ? 'bg-red-500'
                        : 'bg-yellow-500'
                    }`} />
                    <span className="text-xs">
                      {llmHealthStatus[llmProvider]?.status === 'healthy' ? '接続中' : '切断'}
                    </span>
                  </div>
                </div>
                
                {llmHealthStatus[llmProvider]?.models && llmHealthStatus[llmProvider].models.length > 0 && (
                  <div className="mt-2">
                    <p className="text-xs text-gray-600 mb-1">利用可能モデル:</p>
                    <div className="flex flex-wrap gap-1">
                      {llmHealthStatus[llmProvider].models.slice(0, 3).map((model: string, index: number) => (
                        <span key={index} className="text-xs bg-blue-100 text-blue-800 px-1 py-0.5 rounded">
                          {model}
                        </span>
                      ))}
                      {llmHealthStatus[llmProvider].models.length > 3 && (
                        <span className="text-xs text-gray-500">
                          +{llmHealthStatus[llmProvider].models.length - 3} more
                        </span>
                      )}
                    </div>
                  </div>
                )}
                
                {llmHealthStatus[llmProvider]?.status !== 'healthy' && (
                  <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-xs text-yellow-800">
                    {llmHealthStatus[llmProvider]?.message}
                  </div>
                )}
              </div>
            ) : (
              <div className="text-xs text-gray-500">接続状態を確認中...</div>
            )}
          </div>
          
          <div className="p-4">
            <h3 className="text-sm font-medium text-gray-900 mb-3">引用・出典</h3>
            <p className="text-xs text-gray-600">
              AIの応答に関連するドキュメントの引用がここに表示されます
            </p>
          </div>
        </div>
      </div>

      {/* Modals */}
      <TeamSelectorModal
        isOpen={showTeamSelector}
        onClose={() => setShowTeamSelector(false)}
        selectedTeam={selectedTeam}
        onSelectTeam={handleSelectTeam}
        onEditTeam={handleEditTeam}
        onCreateTeam={handleCreateTeam}
        projectId={parseInt(projectId)}
      />

      <TeamEditorModal
        isOpen={showTeamEditor}
        onClose={() => setShowTeamEditor(false)}
        team={editingTeam}
        onSave={handleSaveTeam}
        mode={teamEditorMode}
        projectId={parseInt(projectId)}
      />
    </div>
  )
}

export default function ChatPage() {
  return (
    <AuthWrapper>
      <ChatPageContent />
    </AuthWrapper>
  )
}