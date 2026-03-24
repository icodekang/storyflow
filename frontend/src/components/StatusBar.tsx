import { useStore } from '../store/useStore'

const STATUS_TEXT = {
  idle: '⏸️ 等待开始',
  running: '⚙️ 生成中...',
  paused: '⏳ 等待人工干预',
  done: '✅ 生成完成',
  error: '❌ 出错了',
}

export function StatusBar() {
  const status = useStore((s) => s.status)

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <span className="text-2xl">
          {status === 'running' && '⚙️'}
          {status === 'done' && '✅'}
          {status === 'paused' && '⏳'}
          {status === 'error' && '❌'}
          {status === 'idle' && '⏸️'}
        </span>
        <span className="font-medium text-gray-800">{STATUS_TEXT[status]}</span>
      </div>

      <div className="text-sm text-gray-500">
        {status === 'running' && 'AI Agent 正在工作中，请稍候...'}
        {status === 'paused' && '请在右侧面板完成人工干预'}
        {status === 'done' && '视频已生成完毕'}
        {status === 'idle' && '输入故事文本，点击开始生成'}
        {status === 'error' && '请检查后端服务或重试'}
      </div>
    </div>
  )
}
