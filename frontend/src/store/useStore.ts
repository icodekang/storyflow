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

interface StoryState {
  // Story 数据
  storyText: string
  storyId: string
  sessionId: string
  mode: Mode
  status: 'idle' | 'running' | 'paused' | 'done' | 'error'
  finalOutput: AgentOutput | null

  // Agent 状态
  agents: AgentState[]

  // UI 状态
  interventionDrawerOpen: boolean
  interventionAgent: string | null

  // Actions
  setStoryText: (text: string) => void
  setStoryId: (id: string) => void
  setSessionId: (id: string) => void
  setMode: (mode: Mode) => void
  setStatus: (status: StoryState['status']) => void
  setFinalOutput: (output: AgentOutput | null) => void
  handleWSMessage: (msg: WSMessage) => void
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
  interventionDrawerOpen: false,
  interventionAgent: null,

  setStoryText: (text) => set({ storyText: text }),
  setStoryId: (id) => set({ storyId: id }),
  setSessionId: (id) => set({ sessionId: id }),
  setMode: (mode) => set({ mode }),
  setStatus: (status) => set({ status }),
  setFinalOutput: (output) => set({ finalOutput: output }),

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
        case 'session_state':
          return { status: msg.status as StoryState['status'] }
        default:
          return state
      }
    }),

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
      interventionDrawerOpen: false,
      interventionAgent: null,
    }),
}))
