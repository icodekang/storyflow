import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from './api'
import { useStore } from './store/useStore'
import { useStoryStore } from './stores/storyStore'
import { StoryInputCard } from './components/StoryInputCard'
import { StatusBar } from './components/StatusBar'
import { InterventionDrawer } from './components/InterventionDrawer'
import { StoryList } from './components/StoryList/StoryList'

export default function App() {
  const store = useStore()
  const storyStore = useStoryStore()
  const [loading, setLoading] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  // 全局 WebSocket 连接（所有 story 共享）
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

        // 更新 storyStore 中对应 story 的状态
        if (msg.type === 'agent_status' && msg.agent) {
          storyStore.updateStory(activeId, { status: 'running', currentAgent: msg.agent })
        } else if (msg.type === 'story_complete') {
          storyStore.updateStory(activeId, { status: 'done', currentAgent: null })
        } else if (msg.type === 'story_error') {
          storyStore.updateStory(activeId, { status: 'error', currentAgent: null })
        }
      } catch {}
    }

    ws.onclose = () => wsRef.current = null
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
        status: 'running' as const,
        currentAgent: null,
        createdAt: Date.now(),
      }

      storyStore.addStory(newStory)

      // 通过 WebSocket 触发生成
      const ws = wsRef.current
      if (ws?.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
          type: 'start',
          story_text: store.storyText,
          mode: store.mode,
        }))
      }
    } catch (e) {
      console.error('Start failed:', e)
    } finally {
      setLoading(false)
    }
  }, [store.storyText, store.mode, storyStore])

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

  // 监听 agent waiting 状态，自动打开干预抽屉
  useEffect(() => {
    const waiting = store.agents.find((a) => a.status === 'waiting')
    if (waiting && !store.interventionDrawerOpen) {
      store.openInterventionDrawer(waiting.name)
    }
  }, [store.agents, store.interventionDrawerOpen, store.openInterventionDrawer])

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-8 py-4 flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900">🎬 StoryFlow AI</h1>
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-400">
            {storyStore.stories.length} 个 Story
          </span>
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
        {/* Story 输入区 */}
        <div className="mb-6">
          <StoryInputCard onStart={handleStart} loading={loading} />
        </div>

        {/* 状态栏 */}
        <div className="mb-6">
          <StatusBar />
        </div>

        {/* Story 列表 */}
        <StoryList />
      </main>

      <InterventionDrawer onIntervene={handleIntervene} />
    </div>
  )
}
