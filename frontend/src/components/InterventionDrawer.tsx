import { useState } from 'react'
import { useStore } from '../store/useStore'

interface Props {
  onIntervene: (action: 'confirm' | 'regenerate' | 'skip', feedback: string) => void
}

export function InterventionDrawer({ onIntervene }: Props) {
  const { interventionDrawerOpen, interventionAgent, agents, closeInterventionDrawer } =
    useStore()
  const [feedback, setFeedback] = useState('')

  if (!interventionDrawerOpen) return null

  const agentState = agents.find((a) => a.name === interventionAgent)
  const output = agentState?.output

  return (
    <div className="fixed inset-0 z-50 flex">
      {/* Backdrop */}
      <div className="flex-1 bg-black/30" onClick={closeInterventionDrawer} />

      {/* Drawer */}
      <div className="w-96 bg-white shadow-xl flex flex-col">
        <div className="flex items-center justify-between p-4 border-b">
          <h3 className="font-semibold text-gray-800">
            👤 人工干预 — {interventionAgent}
          </h3>
          <button
            onClick={closeInterventionDrawer}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>

        {/* 当前 Agent 输出预览 */}
        <div className="flex-1 p-4 overflow-auto">
          <p className="text-xs text-gray-500 mb-2">当前输出预览</p>
          <pre className="text-xs bg-gray-50 p-3 rounded-lg overflow-auto max-h-60">
            {JSON.stringify(output, null, 2)}
          </pre>

          {/* 反馈输入 */}
          <div className="mt-4">
            <label className="text-xs text-gray-500 mb-1 block">
              修改建议 / 反馈
            </label>
            <textarea
              className="w-full h-24 p-2 border border-gray-300 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="可选：输入你的修改建议..."
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
            />
          </div>
        </div>

        {/* 操作按钮 */}
        <div className="p-4 border-t flex gap-2">
          <button
            onClick={() => { onIntervene('confirm', ''); closeInterventionDrawer() }}
            className="flex-1 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700"
          >
            ✅ 确认
          </button>
          <button
            onClick={() => { onIntervene('regenerate', feedback); closeInterventionDrawer() }}
            className="flex-1 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700"
          >
            🔄 重新生成
          </button>
          <button
            onClick={() => { onIntervene('skip', ''); closeInterventionDrawer() }}
            className="flex-1 py-2 bg-gray-200 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-300"
          >
            ⏭️ 跳过
          </button>
        </div>
      </div>
    </div>
  )
}
