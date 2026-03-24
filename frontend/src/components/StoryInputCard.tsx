import { useStore } from '../store/useStore'

interface Props {
  onStart: () => void
  loading: boolean
}

export function StoryInputCard({ onStart, loading }: Props) {
  const { storyText, setStoryText, mode, setMode } = useStore()

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-800 mb-4">输入故事文本</h2>

      <textarea
        className="w-full h-40 p-3 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-800"
        placeholder="在这里输入你的故事内容..."
        value={storyText}
        onChange={(e) => setStoryText(e.target.value)}
      />

      <div className="flex items-center justify-between mt-4">
        {/* 模式切换 */}
        <div className="flex gap-2">
          {(['auto', 'human'] as const).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                mode === m
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {m === 'auto' ? '🤖 全自动' : '👤 人工干预'}
            </button>
          ))}
        </div>

        {/* 开始按钮 */}
        <button
          onClick={onStart}
          disabled={!storyText.trim() || loading}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? '生成中...' : '开始生成视频'}
        </button>
      </div>
    </div>
  )
}
