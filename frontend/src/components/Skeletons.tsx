export function SkeletonLine(props: { width?: string; height?: string; className?: string }) {
  const { width = 'w-full', height = 'h-4', className = '' } = props
  return (
    <div className={`bg-gray-200 rounded animate-pulse ${width} ${height} ${className}`} />
  )
}

export function AgentFlowSkeleton() {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="flex items-center gap-2 mb-4">
        <SkeletonLine width="w-24" height="h-5" />
      </div>
      <div className="flex flex-col gap-3">
        {Array.from({ length: 7 }).map((_, i) => (
          <div key={i} className="flex items-center gap-3">
            <SkeletonLine width="w-5" height="h-4" />
            <SkeletonLine width="w-full" height="h-10" />
          </div>
        ))}
      </div>
    </div>
  )
}

export function StoryCardSkeleton() {
  return (
    <div className="p-4 rounded-xl border border-gray-200 bg-white">
      <SkeletonLine width="w-3/4" height="h-4" />
      <div className="flex gap-2 mt-2">
        <SkeletonLine width="w-16" height="h-5" />
        <SkeletonLine width="w-24" height="h-5" />
      </div>
    </div>
  )
}

export function VideoPreviewSkeleton() {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <SkeletonLine width="w-32" height="h-5" className="mb-4" />
      <SkeletonLine width="w-full" height="h-64" />
      <div className="flex gap-3 mt-4">
        <SkeletonLine width="w-full" height="h-2" />
        <SkeletonLine width="w-12" height="h-4" />
      </div>
    </div>
  )
}
