import { useStoryStore } from '../stores/storyStore'

export function QueueStatusBar() {
  const { stories } = useStoryStore()

  const running = stories.filter((s) => s.status === 'running').length
  const queued = stories.filter((s) => s.status === 'queued').length
  const done = stories.filter((s) => s.status === 'done').length
  const paused = stories.filter((s) => s.status === 'paused').length

  if (stories.length === 0) return null

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 px-6 py-3 flex items-center gap-6 text-sm">
      <div className="flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
        <span className="text-gray-600">运行中 <strong className="text-gray-900">{running}</strong></span>
      </div>
      <div className="flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-yellow-500" />
        <span className="text-gray-600">排队中 <strong className="text-gray-900">{queued}</strong></span>
      </div>
      <div className="flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-blue-500" />
        <span className="text-gray-600">等待干预 <strong className="text-gray-900">{paused}</strong></span>
      </div>
      <div className="flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-gray-400" />
        <span className="text-gray-600">已完成 <strong className="text-gray-900">{done}</strong></span>
      </div>
      <div className="ml-auto text-xs text-gray-400">
        最多并发 3 个 story
      </div>
    </div>
  )
}
