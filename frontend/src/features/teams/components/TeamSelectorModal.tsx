'use client'

import { useState, useEffect, useMemo, useCallback } from 'react'
import { Search, Plus, Settings, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { teamsApi, Team, Agent } from '@/features/teams/api'

interface TeamSelectorModalProps {
  isOpen: boolean
  onClose: () => void
  selectedTeam: Team | null
  onSelectTeam: (team: Team) => void
  onEditTeam: (team: Team) => void
  onCreateTeam: () => void
  projectId: number
}

export default function TeamSelectorModal({
  isOpen,
  onClose,
  selectedTeam,
  onSelectTeam,
  onEditTeam,
  onCreateTeam,
  projectId
}: TeamSelectorModalProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [teams, setTeams] = useState<Team[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // プロジェクトのチーム一覧を取得
  const fetchTeams = useCallback(async () => {

    setLoading(true)
    setError('')
    try {
      const response = await teamsApi.getTeamsByProject(projectId)
      setTeams(response.data || [])
    } catch (err: any) {
      console.error('Failed to fetch teams:', err)
      setError('チーム一覧の取得に失敗しました')
      setTeams([])
    } finally {
      setLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    if (isOpen) {
      fetchTeams()
    }
  }, [isOpen, fetchTeams])

  const filteredTeams = useMemo(() => {
    return teams.filter(team =>
      team.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (team.description?.toLowerCase().includes(searchQuery.toLowerCase()) ?? false)
    )
  }, [teams, searchQuery])

  const handleTeamSelect = (team: Team) => {
    onSelectTeam(team)
    onClose()
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>チームを選択</DialogTitle>
        </DialogHeader>

        <div className="flex flex-col space-y-4 flex-1">
          {/* Search and Create Button */}
          <div className="flex space-x-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="チームを検索..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
            <Button onClick={onCreateTeam} variant="outline">
              <Plus className="h-4 w-4 mr-2" />
              新しいチームを作成
            </Button>
          </div>

          {/* Loading State */}
          {loading && (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin mr-2" />
              <span className="text-gray-600">チーム一覧を読み込み中...</span>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-600 text-sm">{error}</p>
              <Button
                onClick={fetchTeams}
                variant="outline"
                size="sm"
                className="mt-2"
              >
                再試行
              </Button>
            </div>
          )}

          {/* Teams List */}
          {!loading && !error && (
            <div className="flex-1 overflow-y-auto space-y-3">
              {filteredTeams.map((team) => (
                <div
                  key={team.id}
                  className={`p-4 border rounded-lg cursor-pointer transition-colors hover:bg-gray-50 ${selectedTeam?.id === team.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200'
                    }`}
                >
                  <div className="flex items-start justify-between">
                    <div
                      className="flex-1 min-w-0"
                      onClick={() => handleTeamSelect(team)}
                    >
                      <div className="flex items-center mb-2">
                        <h3 className="text-sm font-medium text-gray-900">
                          {team.name}
                        </h3>
                        {selectedTeam?.id === team.id && (
                          <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-800 text-xs rounded">
                            現在選択中
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-gray-600 mb-3">
                        {team.description}
                      </p>
                      <div className="flex flex-wrap gap-1">
                        {team.agents.map((agent) => (
                          <span
                            key={agent.id}
                            className="inline-flex items-center px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
                          >
                            {agent.name}
                          </span>
                        ))}
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation()
                        onEditTeam(team)
                      }}
                      className="ml-2 flex-shrink-0"
                    >
                      <Settings className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}

              {filteredTeams.length === 0 && (
                <div className="text-center py-8">
                  <p className="text-gray-500 text-sm">
                    {searchQuery ? '検索結果が見つかりませんでした' : 'チームがありません'}
                  </p>
                  <Button
                    onClick={onCreateTeam}
                    variant="outline"
                    className="mt-2"
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    新しいチームを作成
                  </Button>
                </div>
              )}
            </div>
          )}
          {/* ↑ ここの直後にあった不要な </div> を削除しました */}

          {/* Footer */}
          <div className="flex justify-end pt-3 border-t">
            <Button onClick={onClose} variant="outline">
              閉じる
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}