import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from './api'
import { useStore } from './store/useStore'
import { StoryInputCard } from './components/StoryInputCard'
import { AgentFlow } from './components/AgentFlow'
import { StatusBar } from './components/StatusBar'
import { InterventionDrawer } from './components/InterventionDrawer'
import { VideoPreview } from './components/VideoPreview'

export default function App() {
  const store = useStore()
  const [loading, setLoading] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  const handleStart = useCallback(async () => {
    if (!store.storyText.trim()) return
    setLoading(true)

    try {
      // 1. 创建 story
      const story = await api.createStory(store.storyText, store.mode)

      // 2. 建立 WebSocket
      const ws = new WebSocket(`ws://localhost:8000/ws/stories/${story.story_id}`)
      wsRef.current = ws

      ws.onopen = () => {
        // 3. 通过 WebSocket 触发生成
        ws.send(JSON.stringify({
          type: 'start',
          story_text: store.storyText,
          mode: store.mode,
        }))
      }

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data)
          store.handleWSMessage(msg)
        } catch {}
      }

      ws.onclose = () => {
        wsRef.current = null
        setLoading(false)
      }

      ws.onerror = () => {
        setLoading(false)
      }
    } catch (e) {
      console.error('Start failed:', e)
      setLoading(false)
    }
  }, [store.storyText, store.mode])

  const handleIntervene = useCallback(
    async (action: 'confirm' | 'regenerate' | 'skip', feedback: string) => {
      if (!store.storyId) return
      try {
        // 找到当前处于 waiting 状态的 agent
        const waitingAgent = store.agents.find((a) => a.status === 'waiting')
        if (!waitingAgent) return

        await api.intervene(store.storyId, waitingAgent.name, action, feedback)

        // 同时通过 WebSocket 通知
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
      <header className="bg-white border-b border-gray-200 px-8 py-4">
        <h1 className="text-xl font-bold text-gray-900">🎬 StoryFlow AI</h1>
      </header>

      <main className="max-w-6xl mx-auto px-8 py-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 左侧：输入 + 状态 + 预览 */}
        <div className="flex flex-col gap-6">
          <StoryInputCard onStart={handleStart} loading={loading} />
          <StatusBar />
          <VideoPreview />
        </div>

        {/* 右侧：Agent 流程 */}
        <div className="flex flex-col gap-6">
          <AgentFlow />
        </div>
      </main>

      <InterventionDrawer onIntervene={handleIntervene} />
    </div>
  )
}
