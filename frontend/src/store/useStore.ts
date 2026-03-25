import { create } from 'zustand'
import type { AgentState, AgentOutput, Mode, WSMessage } from '../types'

const AGENT_NAMES = [
  'ScriptAnalysis',
  'PlotDeconstruct',
  'ScenePlanning',
  'CharacterDesign',
  'VisualGen',
  'VideoAssembly',
  'QCReview',
]

export const LLM_PROVIDERS = {
  openai: {
    label: 'OpenAI',
    models: [
      { value: 'gpt-4o', label: 'GPT-4o（最强）' },
      { value: 'gpt-4o-mini', label: 'GPT-4o mini（便宜快速）' },
      { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
    ],
  },
  anthropic: {
    label: 'Anthropic',
    models: [
      { value: 'claude-3-5-sonnet-20241022', label: 'Claude 3.5 Sonnet（最推荐）' },
      { value: 'claude-3-opus-20240229', label: 'Claude 3 Opus' },
      { value: 'claude-3-haiku-20240307', label: 'Claude 3 Haiku（最快）' },
    ],
  },
}

export type LLMConfig = { provider: 'openai' | 'anthropic'; model: string }

export type AgentLLMConfig = Record<string, LLMConfig>

const DEFAULT_AGENT_CONFIG: AgentLLMConfig = {
  ScriptAnalysis:   { provider: 'openai', model: 'gpt-4o' },
  PlotDeconstruct:  { provider: 'openai', model: 'gpt-4o' },
  ScenePlanning:    { provider: 'openai', model: 'gpt-4o-mini' },
  CharacterDesign:  { provider: 'openai', model: 'gpt-4o' },
  VisualGen:       { provider: 'openai', model: 'gpt-4o' },
  VideoAssembly:   { provider: 'openai', model: 'gpt-4o' },
  QCReview:        { provider: 'anthropic', model: 'claude-3-5-sonnet-20241022' },
}

interface StoryState {
  // Story 数据
  storyText: string
  storyId: string
  sessionId: string
  mode: Mode
  status: 'idle' | 'queued' | 'running' | 'paused' | 'done' | 'error'
  finalOutput: AgentOutput | null

  // Agent 状态
  agents: AgentState[]

  // Agent LLM 配置
  agentLLMConfig: AgentLLMConfig

  // UI 状态
  settingsOpen: boolean
  interventionDrawerOpen: boolean
  interventionAgent: string | null

  // Actions
  setStoryText: (text: string) => void
  setStoryId: (id: string) => void
  setSessionId: (id: string) => void
  setMode: (mode: Mode) => void
  setStatus: (status: StoryState['status']) => void
  setFinalOutput: (output: AgentOutput | null) => void
  setAgentLLMConfig: (agent: string, config: LLMConfig) => void
  resetAgentLLMConfig: () => void
  handleWSMessage: (msg: WSMessage) => void
  openSettings: () => void
  closeSettings: () => void
  openInterventionDrawer: (agentName: string) => void
  closeInterventionDrawer: () => void
  reset: () => void
}

const initialAgents: AgentState[] = AGENT_NAMES.map((name) => ({
  name,
  status: 'idle',
}))

export const useStore = create<StoryState>((set) => ({
  storyText: '',
  storyId: '',
  sessionId: '',
  mode: 'auto',
  status: 'idle',
  finalOutput: null,
  agents: initialAgents,
  agentLLMConfig: { ...DEFAULT_AGENT_CONFIG },
  settingsOpen: false,
  interventionDrawerOpen: false,
  interventionAgent: null,

  setStoryText: (text) => set({ storyText: text }),
  setStoryId: (id) => set({ storyId: id }),
  setSessionId: (id) => set({ sessionId: id }),
  setMode: (mode) => set({ mode }),
  setStatus: (status) => set({ status }),
  setFinalOutput: (output) => set({ finalOutput: output }),

  setAgentLLMConfig: (agent, config) =>
    set((state) => ({
      agentLLMConfig: { ...state.agentLLMConfig, [agent]: config },
    })),

  resetAgentLLMConfig: () =>
    set({ agentLLMConfig: { ...DEFAULT_AGENT_CONFIG } }),

  handleWSMessage: (msg) =>
    set((state) => {
      switch (msg.type) {
        case 'agent_status':
          return {
            agents: state.agents.map((a) =>
              a.name === msg.agent ? { ...a, status: 'running' } : a,
            ),
            status: 'running',
          }
        case 'agent_output':
          return {
            agents: state.agents.map((a) =>
              a.name === msg.agent
                ? { ...a, status: 'done', output: msg.output }
                : a,
            ),
          }
        case 'agent_waiting':
          return {
            agents: state.agents.map((a) =>
              a.name === msg.agent
                ? { ...a, status: 'waiting', output: msg.output }
                : a,
            ),
            status: 'paused',
          }
        case 'story_complete':
          return {
            status: 'done',
            finalOutput: msg.final_output ?? null,
            agents: state.agents.map((a) => ({ ...a, status: 'done' })),
          }
        case 'story_error':
          return { status: 'error' }
        case 'started':
          return {
            storyId: msg.story_id || state.storyId,
            status: 'running',
          }
        case 'job_queued':
          return {
            storyId: msg.story_id || state.storyId,
            status: 'queued',
          }
        case 'session_state':
          return { status: msg.status as StoryState['status'] }
        default:
          return state
      }
    }),

  openSettings: () => set({ settingsOpen: true }),
  closeSettings: () => set({ settingsOpen: false }),

  openInterventionDrawer: (agentName) =>
    set({ interventionDrawerOpen: true, interventionAgent: agentName }),
  closeInterventionDrawer: () =>
    set({ interventionDrawerOpen: false, interventionAgent: null }),

  reset: () =>
    set({
      storyText: '',
      storyId: '',
      sessionId: '',
      status: 'idle',
      finalOutput: null,
      agents: initialAgents,
      agentLLMConfig: { ...DEFAULT_AGENT_CONFIG },
      settingsOpen: false,
      interventionDrawerOpen: false,
      interventionAgent: null,
    }),
}))
