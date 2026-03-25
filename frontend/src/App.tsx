import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from './api'
import { useStore } from './store/useStore'
import { useStoryStore } from './stores/storyStore'
import { StoryInputCard } from './components/StoryInputCard'
import { StatusBar } from './components/StatusBar'
import { QueueStatusBar } from './components/QueueStatusBar'
import { InterventionDrawer } from './components/InterventionDrawer'
import { StoryList } from './components/StoryList/StoryList'
import { SettingsModal } from './components/SettingsModal'

export default function App() {
  const store = useStore()
  const storyStore = useStoryStore()
  const [loading, setLoading] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  // WebSocket 连接（story 切换时重连）
  useEffect(() => {
    const activeId = storyStore.activeStoryId
    if (!activeId) return

    const existingWs = wsRef.current
    if (existingWs) existingWs.close()

    const ws = new WebSocket(`ws://localhost:8000/ws/stories/${activeId}`)
    wsRef.current = ws

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        store.handleWSMessage(msg)

        if (msg.type === 'agent_status' && msg.agent) {
          storyStore.updateStory(activeId, { status: 'running', currentAgent: msg.agent })
        } else if (msg.type === 'job_queued') {
          storyStore.updateStory(activeId, { status: 'queued', jobId: msg.job_id, queuePosition: msg.position })
        } else if (msg.type === 'job_started') {
          storyStore.updateStory(activeId, { status: 'running', jobId: msg.job_id })
        } else if (msg.type === 'story_complete') {
          storyStore.updateStory(activeId, { status: 'done', currentAgent: null })
        } else if (msg.type === 'story_error') {
          storyStore.updateStory(activeId, { status: 'error', currentAgent: null })
        } else if (msg.type === 'job_error') {
          storyStore.updateStory(activeId, { status: 'error' })
        }
      } catch {}
    }

    ws.onclose = () => { wsRef.current = null }
    return () => ws.close()
  }, [storyStore.activeStoryId])

  const handleStart = useCallback(async () => {
    if (!store.storyText.trim()) return
    setLoading(true)

    try {
      const story = await api.createStory(store.storyText, store.mode)

      const newStory = {
        storyId: story.story_id,
        sessionId: story.session_id,
        storyText: store.storyText,
        title: store.storyText.slice(0, 30),
        mode: story.mode as 'auto' | 'human',
        status: 'queued' as const,
        currentAgent: null,
        jobId: null,
        queuePosition: 0,
        createdAt: Date.now(),
      }

      storyStore.addStory(newStory)

      const ws = wsRef.current
      if (ws?.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
          type: 'start',
          story_text: store.storyText,
          mode: store.mode,
          // 发送 Agent LLM 配置到后端
          agent_llm_config: store.agentLLMConfig,
        }))
      }
    } catch (e) {
      console.error('Start failed:', e)
    } finally {
      setLoading(false)
    }
  }, [store.storyText, store.mode, store.agentLLMConfig, storyStore])

  const handleIntervene = useCallback(
    async (action: 'confirm' | 'regenerate' | 'skip', feedback: string) => {
      if (!store.storyId) return
      const waitingAgent = store.agents.find((a) => a.status === 'waiting')
      if (!waitingAgent) return

      try {
        await api.intervene(store.storyId, waitingAgent.name, action, feedback)
        wsRef.current?.send(JSON.stringify({
          type: 'intervene',
          agent_name: waitingAgent.name,
          action,
          feedback,
        }))
      } catch (e) {
        console.error('Intervene failed:', e)
      }
    },
    [store.storyId, store.agents],
  )

  // agent 进入 waiting 状态时自动打开干预抽屉
  useEffect(() => {
    const waiting = store.agents.find((a) => a.status === 'waiting')
    if (waiting && !store.interventionDrawerOpen) {
      store.openInterventionDrawer(waiting.name)
    }
  }, [store.agents, store.interventionDrawerOpen, store.openInterventionDrawer])

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-8 py-4 flex items-center justify-between sticky top-0 z-40">
        <h1 className="text-xl font-bold text-gray-900">🎬 StoryFlow AI</h1>

        <div className="flex items-center gap-3">
          {/* Agent 模型配置按钮 */}
          <button
            onClick={store.openSettings}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
          >
            ⚙️ 模型配置
          </button>

          <span className="text-xs text-gray-400">
            {storyStore.stories.length} 个 Story
          </span>

          {/* 模式切换 */}
          <div className="flex gap-1">
            {(['auto', 'human'] as const).map((m) => (
              <button
                key={m}
                onClick={() => store.setMode(m)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                  store.mode === m
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                }`}
              >
                {m === 'auto' ? '⚡ 全自动' : '👤 人工干预'}
              </button>
            ))}
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-8 py-8">
        <div className="mb-6">
          <StoryInputCard onStart={handleStart} loading={loading} />
        </div>
        <div className="mb-6">
          <StatusBar />
        </div>
        <div className="mb-6">
          <QueueStatusBar />
        </div>
        <StoryList />
      </main>

      <SettingsModal />
      <InterventionDrawer onIntervene={handleIntervene} />
    </div>
  )
}
