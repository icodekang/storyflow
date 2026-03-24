// API 客户端
const BASE = '/api'

async function post<T = unknown>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`API error: ${res.status} ${path}`)
  return res.json()
}

async function get<T = unknown>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`API error: ${res.status} ${path}`)
  return res.json()
}

export interface CreateStoryResponse {
  story_id: string
  session_id: string
  status: string
  mode: string
}

export interface StartGenerateResponse {
  status: string
  story_id: string
  session_id: string
}

export interface AgentOutputResponse {
  agent: string
  output: Record<string, unknown>
}

export const api = {
  createStory: (storyText: string, mode: 'auto' | 'human', title?: string) =>
    post<CreateStoryResponse>('/stories', { story_text: storyText, mode, title }),

  startGenerate: (storyId: string, storyText: string, mode: 'auto' | 'human') =>
    post<StartGenerateResponse>(`/stories/${storyId}/generate`, { story_text: storyText, mode }),

  getStory: (storyId: string) =>
    get<{ story_id: string; session_id: string; status: string; current_agent?: string; mode: string }>(`/stories/${storyId}`),

  getAgentOutput: (storyId: string, agentName: string) =>
    get<AgentOutputResponse>(`/agents/${storyId}/${agentName}/output`),

  intervene: (storyId: string, agentName: string, action: string, feedback?: string) =>
    post(`/agents/${storyId}/${agentName}/intervene`, { action, feedback }),
}
