import { useCallback, useState } from 'react'
import { useStoryStore, type Story } from '../../stores/storyStore'
import { useStore } from '../../store/useStore'
import { api } from '../../api'
import { AgentFlow } from '../AgentFlow'
import { VideoPreview } from '../VideoPreview'

const STATUS_BADGE = {
  idle: { label: '待生成', cls: 'bg-gray-100 text-gray-500' },
  queued: { label: '排队中', cls: 'bg-yellow-50 text-yellow-600' },
  running: { label: '生成中', cls: 'bg-blue-50 text-blue-600 animate-pulse' },
  paused: { label: '等待干预', cls: 'bg-orange-50 text-orange-600' },
  done: { label: '已完成', cls: 'bg-green-50 text-green-600' },
  error: { label: '失败', cls: 'bg-red-50 text-red-600' },
}

function StoryCard({ story, onSelect, onDelete, isActive }: {
  story: Story
  onSelect: () => void
  onDelete: () => void
  isActive: boolean
}) {
  const badge = STATUS_BADGE[story.status]

  return (
    <div
      onClick={onSelect}
      className={`relative p-4 rounded-xl border cursor-pointer transition-all ${
        isActive
          ? 'border-blue-400 bg-blue-50 shadow-sm'
          : 'border-gray-200 bg-white hover:border-gray-300'
      }`}
    >
      <button
        onClick={(e) => { e.stopPropagation(); onDelete() }}
        className="absolute top-3 right-3 text-gray-400 hover:text-red-500 text-sm"
      >
        ✕
      </button>

      <h3 className="font-medium text-gray-800 text-sm pr-6 truncate">
        {story.title || story.storyText.slice(0, 30)}
      </h3>

      <div className="flex items-center gap-2 mt-2">
        <span className={`text-xs px-2 py-0.5 rounded-full ${badge.cls}`}>
          {badge.label}
        </span>
        {story.currentAgent && story.status === 'running' && (
          <span className="text-xs text-gray-400 truncate">
            → {story.currentAgent}
          </span>
        )}
      </div>
    </div>
  )
}

export function StoryList() {
  const { stories, activeStoryId, addStory, removeStory, setActiveStory } =
    useStoryStore()
  const globalStore = useStore()
  const [creating, setCreating] = useState(false)

  const handleAddStory = useCallback(async () => {
    setCreating(true)
    try {
      const text = `新故事 ${Date.now()}`
      const story = await api.createStory(text, globalStore.mode)
      const newStory: Story = {
        storyId: story.story_id,
        sessionId: story.session_id,
        storyText: text,
        title: `故事 ${stories.length + 1}`,
        mode: story.mode as 'auto' | 'human',
        status: 'idle',
        currentAgent: null,
        jobId: null,
        queuePosition: 0,
        createdAt: Date.now(),
      }
      addStory(newStory)
    } finally {
      setCreating(false)
    }
  }, [stories.length, globalStore.mode, addStory])

  const handleSelect = useCallback((id: string) => {
    setActiveStory(id)
  }, [setActiveStory])

  const handleDelete = useCallback((id: string) => {
    removeStory(id)
  }, [removeStory])

  const activeStory = stories.find((s) => s.storyId === activeStoryId)

  return (
    <div className="space-y-4">
      {/* Story 卡片列表 */}
      <div className="grid grid-cols-2 gap-3">
        {stories.map((s) => (
          <StoryCard
            key={s.storyId}
            story={s}
            onSelect={() => handleSelect(s.storyId)}
            onDelete={() => handleDelete(s.storyId)}
            isActive={s.storyId === activeStoryId}
          />
        ))}

        {/* 新增按钮 */}
        <button
          onClick={handleAddStory}
          disabled={creating}
          className="p-4 rounded-xl border-2 border-dashed border-gray-300 text-gray-400 hover:border-blue-400 hover:text-blue-500 transition-colors flex flex-col items-center justify-center gap-1"
        >
          <span className="text-xl">+</span>
          <span className="text-xs">新增 Story</span>
        </button>
      </div>

      {/* 活跃 Story 的详情 */}
      {activeStory && (
        <div className="space-y-4">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
            <p className="text-sm text-gray-600 line-clamp-2">{activeStory.storyText}</p>
          </div>
          <AgentFlow />
          <VideoPreview />
        </div>
      )}

      {/* 空状态 */}
      {stories.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-gray-400">
          <span className="text-5xl mb-4">📖</span>
          <p className="text-lg font-medium">还没有任何 Story</p>
          <p className="text-sm mt-1">点击上方 "+ 新增 Story" 开始</p>
        </div>
      )}
    </div>
  )
}
