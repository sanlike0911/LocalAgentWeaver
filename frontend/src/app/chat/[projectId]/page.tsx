'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { useParams } from 'next/navigation'
import { Send, ArrowLeft, Bot, User } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { projectApi, chatApi, Project } from '@/utils/api'

interface Message {
  id: string
  content: string
  sender: 'user' | 'assistant'
  timestamp: Date
}

export default function ChatPage() {
  const [project, setProject] = useState<Project | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [llmProvider, setLlmProvider] = useState<'ollama' | 'lm_studio'>('ollama')
  const [selectedModel, setSelectedModel] = useState('llama3')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const router = useRouter()
  const params = useParams()
  const projectId = params.projectId as string

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) {
      router.push('/auth/login')
      return
    }

    fetchProject()
  }, [projectId, router])

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

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
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

    try {
      const response = await chatApi.sendMessage({
        project_id: projectId,
        message: userMessage.content,
        provider: llmProvider,
        model: selectedModel
      })
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response.data.message,
        sender: 'assistant',
        timestamp: new Date()
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (err: any) {
      setError(err.response?.data?.detail || 'メッセージの送信に失敗しました')
      
      // フォールバック応答
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: `申し訳ございません。LLMサーバーに接続できませんでした。Ollama/LM Studioが起動していることを確認してください。`,
        sender: 'assistant',
        timestamp: new Date()
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
    <div className="min-h-screen bg-gray-50 flex flex-col">
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

      <div className="flex-1 max-w-4xl mx-auto w-full px-4 py-6 flex flex-col">
        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded">
            {error}
          </div>
        )}

        <Card className="flex-1 flex flex-col">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center">
                <Bot className="mr-2 h-5 w-5" />
                AIアシスタント
              </div>
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <label className="text-sm font-medium">Provider:</label>
                  <select 
                    value={llmProvider}
                    onChange={(e) => setLlmProvider(e.target.value as 'ollama' | 'lm_studio')}
                    className="text-sm border rounded px-2 py-1"
                  >
                    <option value="ollama">Ollama</option>
                    <option value="lm_studio">LM Studio</option>
                  </select>
                </div>
                <div className="flex items-center space-x-2">
                  <label className="text-sm font-medium">Model:</label>
                  <input 
                    type="text"
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    className="text-sm border rounded px-2 py-1 w-24"
                    placeholder="llama3"
                  />
                </div>
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col">
            <div className="flex-1 overflow-y-auto mb-4 space-y-4 max-h-96">
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
                      <p className={`text-xs mt-1 ${
                        message.sender === 'user' 
                          ? 'text-primary-foreground/70' 
                          : 'text-gray-500'
                      }`}>
                        {message.timestamp.toLocaleTimeString('ja-JP', { 
                          hour: '2-digit', 
                          minute: '2-digit' 
                        })}
                      </p>
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
    </div>
  )
}