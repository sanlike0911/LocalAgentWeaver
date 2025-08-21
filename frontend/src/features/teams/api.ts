import { api } from '@/utils/api'

// Types
export interface Agent {
  id: string
  name: string
  role: string
  system_prompt?: string
  created_at: string
  updated_at: string
}

export interface Team {
  id: string
  name: string
  description?: string
  project_id: string
  agents: Agent[]
  created_at: string
  updated_at: string
}

export interface AgentPreset {
  name: string
  role: string
  system_prompt: string
  description: string
  category: string
}

export interface TeamPreset {
  name: string
  description: string
  agents: string[]
  category: string
}

export interface CreateTeamRequest {
  name: string
  description?: string
  project_id: number
  agent_ids?: number[]
}

export interface UpdateTeamRequest {
  name?: string
  description?: string
  agent_ids?: number[]
}

export interface CreateAgentRequest {
  name: string
  role: string
  system_prompt?: string
}

export interface UpdateAgentRequest {
  name?: string
  role?: string
  system_prompt?: string
}

// Teams API
export const teamsApi = {
  // Team operations
  getTeamsByProject: (projectId: number) =>
    api.get(`/api/projects/${projectId}/teams`),

  getTeam: (teamId: number) => 
    api.get(`/api/teams/${teamId}`),

  createTeam: (data: CreateTeamRequest) =>
    api.post('/api/teams', data),

  updateTeam: (teamId: number, data: UpdateTeamRequest) =>
    api.put(`/api/teams/${teamId}`, data),

  deleteTeam: (teamId: number) =>
    api.delete(`/api/teams/${teamId}`),

  // Agent operations
  getAllAgents: () =>
    api.get('/api/agents'),

  getAgent: (agentId: number) =>
    api.get(`/api/agents/${agentId}`),

  createAgent: (data: CreateAgentRequest) =>
    api.post('/api/agents', data),

  updateAgent: (agentId: number, data: UpdateAgentRequest) =>
    api.put(`/api/agents/${agentId}`, data),

  deleteAgent: (agentId: number) =>
    api.delete(`/api/agents/${agentId}`),

  // Preset operations
  getAgentPresets: (category?: string) =>
    api.get('/api/presets/agents', { params: category ? { category } : {} }),

  getTeamPresets: (category?: string) =>
    api.get('/api/presets/teams', { params: category ? { category } : {} }),

  getPresetCategories: () =>
    api.get('/api/presets/categories'),

  instantiateAgentPreset: (presetName: string) =>
    api.post(`/api/presets/agents/${encodeURIComponent(presetName)}/instantiate`),

  instantiateTeamPreset: (presetName: string, projectId: number) =>
    api.post(`/api/presets/teams/${encodeURIComponent(presetName)}/instantiate`, null, {
      params: { project_id: projectId }
    }),
}

export default teamsApi