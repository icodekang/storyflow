import { useStore } from '../store/useStore'

export function VideoPreview() {
  const { status, finalOutput } = useStore()

  if (status !== 'done') return null

  const videoPath = finalOutput?.data?.final_video_path as string | undefined
  const qualityScore = finalOutput?.data?.quality_score as number | undefined

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-800 mb-4">🎬 视频预览</h2>

      {videoPath ? (
        <video
          src={`http://localhost:8000${videoPath}`}
          controls
          className="w-full rounded-lg"
        />
      ) : (
        <div className="flex flex-col items-center justify-center h-48 bg-gray-50 rounded-lg text-gray-400">
          <span className="text-4xl mb-2">🎥</span>
          <p className="text-sm">视频文件路径未找到</p>
        </div>
      )}

      {qualityScore !== undefined && (
        <div className="mt-4 flex items-center gap-3">
          <span className="text-sm text-gray-600">质量评分：</span>
          <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-green-500 transition-all"
              style={{ width: `${qualityScore}%` }}
            />
          </div>
          <span className="text-sm font-medium text-gray-700">{qualityScore}/100</span>
        </div>
      )}
    </div>
  )
}
