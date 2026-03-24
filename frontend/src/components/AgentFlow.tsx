import { useStore } from '../store/useStore'

const AGENT_LABELS: Record<string, string> = {
  ScriptAnalysis: '📝 剧本分析',
  PlotDeconstruct: '🔱 情节拆解',
  ScenePlanning: '🎬 分镜规划',
  CharacterDesign: '👤 角色设计',
  VisualGen: '🎨 视觉生成',
  VideoAssembly: '🎞️ 视频剪辑',
  QCReview: '✅ 质检复审',
}

const STATUS_STYLES = {
  idle: 'bg-gray-100 text-gray-400 border-gray-200',
  running: 'bg-blue-50 text-blue-600 border-blue-300 animate-pulse',
  waiting: 'bg-yellow-50 text-yellow-600 border-yellow-300',
  done: 'bg-green-50 text-green-600 border-green-300',
}

export function AgentFlow() {
  const agents = useStore((s) => s.agents)

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-800 mb-4">Agent 执行流程</h2>

      <div className="flex flex-col gap-3">
        {agents.map((agent, idx) => (
          <div key={agent.name} className="flex items-center gap-3">
            {/* 序号 */}
            <span className="text-xs text-gray-400 w-5">{idx + 1}</span>

            {/* 连接线（除了第一个） */}
            {idx > 0 && (
              <div className="absolute left-[22px] top-0 w-0.5 h-3 -translate-y-full bg-gray-200" />
            )}

            {/* Agent 卡片 */}
            <div
              className={`flex-1 flex items-center justify-between px-4 py-3 rounded-lg border transition-all ${STATUS_STYLES[agent.status]}`}
            >
              <span className="font-medium text-sm">
                {AGENT_LABELS[agent.name] ?? agent.name}
              </span>

              <span className="text-xs">
                {agent.status === 'idle' && '⏸️'}
                {agent.status === 'running' && '⚙️'}
                {agent.status === 'waiting' && '⏳'}
                {agent.status === 'done' && '✅'}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
