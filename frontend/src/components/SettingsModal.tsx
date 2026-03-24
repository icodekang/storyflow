import { useStore, LLM_PROVIDERS } from '../store/useStore'

const AGENT_LABELS: Record<string, string> = {
  ScriptAnalysis: '📝 剧本分析',
  PlotDeconstruct: '🔱 情节拆解',
  ScenePlanning: '🎬 分镜规划',
  CharacterDesign: '👤 角色设计',
  VisualGen: '🎨 视觉生成',
  VideoAssembly: '🎞️ 视频剪辑',
  QCReview: '✅ 质检复审',
}

export function SettingsModal() {
  const { settingsOpen, closeSettings, agentLLMConfig, setAgentLLMConfig, resetAgentLLMConfig } =
    useStore()

  if (!settingsOpen) return null

  const handleProviderChange = (agent: string, provider: 'openai' | 'anthropic') => {
    const firstModel = LLM_PROVIDERS[provider].models[0].value
    setAgentLLMConfig(agent, { provider, model: firstModel })
  }

  const handleModelChange = (agent: string, model: string) => {
    const current = agentLLMConfig[agent]
    setAgentLLMConfig(agent, { ...current, model })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={closeSettings} />

      {/* Modal */}
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <div>
            <h2 className="text-lg font-bold text-gray-900">⚙️ Agent 模型配置</h2>
            <p className="text-xs text-gray-500 mt-0.5">为每个 Agent 选择使用的大模型</p>
          </div>
          <button
            onClick={closeSettings}
            className="text-gray-400 hover:text-gray-600 text-xl leading-none"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-auto px-6 py-4">
          <div className="space-y-3">
            {Object.entries(agentLLMConfig).map(([agent, config]) => (
              <div
                key={agent}
                className="flex items-center gap-4 p-3 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors"
              >
                {/* Agent 名称 */}
                <div className="w-36 flex-shrink-0">
                  <span className="text-sm font-medium text-gray-700">
                    {AGENT_LABELS[agent] ?? agent}
                  </span>
                </div>

                {/* Provider 选择 */}
                <div className="flex gap-1">
                  {(Object.keys(LLM_PROVIDERS) as Array<'openai' | 'anthropic'>).map(
                    (provider) => (
                      <button
                        key={provider}
                        onClick={() => handleProviderChange(agent, provider)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                          config.provider === provider
                            ? provider === 'openai'
                              ? 'bg-green-500 text-white'
                              : 'bg-orange-500 text-white'
                            : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                        }`}
                      >
                        {LLM_PROVIDERS[provider].label}
                      </button>
                    ),
                  )}
                </div>

                {/* Model 选择 */}
                <select
                  value={config.model}
                  onChange={(e) => handleModelChange(agent, e.target.value)}
                  className="flex-1 h-8 px-2 text-sm border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700"
                >
                  {LLM_PROVIDERS[config.provider].models.map((m) => (
                    <option key={m.value} value={m.value}>
                      {m.label}
                    </option>
                  ))}
                </select>
              </div>
            ))}
          </div>

          {/* 说明 */}
          <div className="mt-4 p-3 bg-blue-50 rounded-xl text-xs text-blue-700">
            💡 配置将跟随每次生成请求发送到后端。后端必须已配置对应模型的 API Key 才能正常工作。
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t bg-gray-50 rounded-b-2xl">
          <button
            onClick={resetAgentLLMConfig}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            重置为默认
          </button>
          <button
            onClick={closeSettings}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            保存并关闭
          </button>
        </div>
      </div>
    </div>
  )
}
