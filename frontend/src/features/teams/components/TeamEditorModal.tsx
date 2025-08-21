'use client'

import { useState, useEffect } from 'react'
import { Plus, Trash2, Copy, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { teamsApi, Team, Agent, CreateTeamRequest, UpdateTeamRequest } from '@/features/teams/api'

interface TeamEditorModalProps {
  isOpen: boolean
  onClose: () => void
  team: Team | null
  onSave: (team: Team) => void
  mode: 'create' | 'edit'
  projectId: number
}

export default function TeamEditorModal({
  isOpen,
  onClose,
  team,
  onSave,
  mode,
  projectId
}: TeamEditorModalProps) {
  const [teamName, setTeamName] = useState('')
  const [teamDescription, setTeamDescription] = useState('')
  const [agents, setAgents] = useState<Agent[]>([])
  const [selectedCopyTeam, setSelectedCopyTeam] = useState<string>('')
  const [availableTeams, setAvailableTeams] = useState<Team[]>([])
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  // 他のチーム一覧を取得
  const fetchAvailableTeams = async () => {
    if (!projectId) return
    
    setLoading(true)
    try {
      const response = await teamsApi.getTeamsByProject(projectId)
      setAvailableTeams(response.data || [])
    } catch (err: any) {
      console.error('Failed to fetch teams:', err)
      setError('チーム一覧の取得に失敗しました')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isOpen && projectId) {
      fetchAvailableTeams()
    }
  }, [isOpen, projectId])

  useEffect(() => {
    if (team && mode === 'edit') {
      setTeamName(team.name)
      setTeamDescription(team.description)
      setAgents([...team.agents])
    } else {
      // Reset form for create mode
      setTeamName('')
      setTeamDescription('')
      setAgents([])
    }
  }, [team, mode, isOpen])

  const addAgent = () => {
    const newAgent: Agent = {
      id: Date.now().toString(),
      name: '',
      role: ''
    }
    setAgents([...agents, newAgent])
  }

  const updateAgent = (index: number, field: keyof Agent, value: string) => {
    const updatedAgents = [...agents]
    updatedAgents[index] = { ...updatedAgents[index], [field]: value }
    setAgents(updatedAgents)
  }

  const removeAgent = (index: number) => {
    setAgents(agents.filter((_, i) => i !== index))
  }

  const copyAgentsFromTeam = () => {
    const sourceTeam = availableTeams.find(t => t.id === selectedCopyTeam)
    if (sourceTeam) {
      const copiedAgents = sourceTeam.agents.map(agent => ({
        ...agent,
        id: Date.now().toString() + Math.random() // Generate new IDs
      }))
      setAgents([...agents, ...copiedAgents])
      setSelectedCopyTeam('')
    }
  }

  const handleSave = async () => {
    if (!teamName.trim()) return

    setSaving(true)
    setError('')

    try {
      const validAgents = agents.filter(agent => agent.name.trim() && agent.role.trim())
      
      if (mode === 'create') {
        // 新規作成
        const createData: CreateTeamRequest = {
          name: teamName.trim(),
          description: teamDescription.trim(),
          project_id: projectId,
          // エージェント作成は別途処理が必要（簡略化のため省略）
        }
        
        const response = await teamsApi.createTeam(createData)
        onSave(response.data)
      } else if (team) {
        // 更新
        const updateData: UpdateTeamRequest = {
          name: teamName.trim(),
          description: teamDescription.trim(),
          // エージェント更新は別途処理が必要（簡略化のため省略）
        }
        
        const response = await teamsApi.updateTeam(parseInt(team.id), updateData)
        onSave(response.data)
      }
      
      onClose()
    } catch (err: any) {
      console.error('Failed to save team:', err)
      setError('チームの保存に失敗しました')
    } finally {
      setSaving(false)
    }
  }

  const isValid = teamName.trim() && agents.some(agent => agent.name.trim() && agent.role.trim())

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>
            {mode === 'create' ? 'チームを作成' : 'チームを編集'}
          </DialogTitle>
        </DialogHeader>

        <div className="flex flex-col space-y-6 flex-1 overflow-y-auto">
          {/* Error State */}
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-600 text-sm">{error}</p>
            </div>
          )}

          {/* Basic Info */}
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-700">チーム名</label>
              <Input
                value={teamName}
                onChange={(e) => setTeamName(e.target.value)}
                placeholder="開発チーム"
                className="mt-1"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">チームの役割・目的</label>
              <textarea
                value={teamDescription}
                onChange={(e) => setTeamDescription(e.target.value)}
                placeholder="このチームは..."
                className="mt-1 w-full p-2 border border-gray-300 rounded-md text-sm min-h-[80px] resize-none"
              />
            </div>
          </div>

          {/* Agents Section */}
          <div className="border-t pt-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-gray-900">エージェント</h3>
              <Button onClick={addAgent} variant="outline" size="sm">
                <Plus className="h-4 w-4 mr-2" />
                エージェントを追加
              </Button>
            </div>

            <div className="space-y-3">
              {agents.map((agent, index) => (
                <div key={agent.id} className="flex items-start space-x-3 p-3 border rounded-lg">
                  <div className="flex-1 space-y-2">
                    <Input
                      placeholder="エージェント名"
                      value={agent.name}
                      onChange={(e) => updateAgent(index, 'name', e.target.value)}
                      className="text-sm"
                    />
                    <textarea
                      placeholder="役割・専門性"
                      value={agent.role}
                      onChange={(e) => updateAgent(index, 'role', e.target.value)}
                      className="w-full p-2 border border-gray-300 rounded-md text-sm min-h-[60px] resize-none"
                    />
                  </div>
                  <Button
                    onClick={() => removeAgent(index)}
                    variant="ghost"
                    size="sm"
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          </div>

          {/* Copy from Other Teams */}
          <div className="border-t pt-6">
            <h3 className="text-sm font-medium text-gray-900 mb-4">
              他のチームからエージェントをコピー
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-700">コピー元チーム</label>
                <select
                  value={selectedCopyTeam}
                  onChange={(e) => setSelectedCopyTeam(e.target.value)}
                  className="mt-1 w-full p-2 border border-gray-300 rounded-md text-sm"
                >
                  <option value="">チームを選択してください</option>
                  {availableTeams
                    .filter(t => t.id !== team?.id) // 編集中のチームは除外
                    .map((availableTeam) => (
                    <option key={availableTeam.id} value={availableTeam.id}>
                      {availableTeam.name}
                    </option>
                  ))}
                </select>
              </div>

              {selectedCopyTeam && (
                <div className="p-3 bg-gray-50 rounded-lg">
                  <div className="mb-2">
                    <p className="text-sm font-medium text-gray-900">
                      {availableTeams.find(t => t.id === selectedCopyTeam)?.name}
                    </p>
                    <p className="text-xs text-gray-600">
                      {availableTeams.find(t => t.id === selectedCopyTeam)?.description}
                    </p>
                  </div>
                  <div className="space-y-2">
                    <p className="text-xs font-medium text-gray-700">エージェント:</p>
                    <div className="flex flex-wrap gap-2">
                      {availableTeams.find(t => t.id === selectedCopyTeam)?.agents.map((agent) => (
                        <div key={agent.id} className="text-xs bg-white px-2 py-1 rounded border">
                          <span className="font-medium">{agent.name}</span>
                          <span className="text-gray-600"> - {agent.role}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <Button
                    onClick={copyAgentsFromTeam}
                    variant="outline"
                    size="sm"
                    className="mt-3"
                  >
                    <Copy className="h-4 w-4 mr-2" />
                    選択したエージェントをコピー
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-between pt-6 border-t">
          <Button onClick={onClose} variant="outline" disabled={saving}>
            キャンセル
          </Button>
          <Button onClick={handleSave} disabled={!isValid || saving}>
            {saving ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                保存中...
              </>
            ) : (
              '保存'
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}