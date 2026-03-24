// 统一类型定义

export type Mode = 'auto' | 'human'
export type SessionStatus = 'running' | 'paused' | 'done' | 'error'

export interface AgentOutput {
  agent_name: string
  timestamp: string
  data: Record<string, unknown>
}

export interface WSMessage {
  type: 'agent_status' | 'agent_output' | 'agent_waiting' | 'story_complete' | 'story_error' | 'pong' | 'started' | 'session_state' | 'intervention_received'
  agent?: string
  status?: string
  output?: AgentOutput
  final_output?: AgentOutput
  error?: string
  story_id?: string
}

export interface Story {
  story_id: string
  session_id: string
  status: SessionStatus
  mode: Mode
  current_agent?: string
}

export interface AgentState {
  name: string
  status: 'idle' | 'running' | 'done' | 'waiting'
  output?: AgentOutput
}
