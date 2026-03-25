import { create } from 'zustand'

export interface Story {
  storyId: string
  sessionId: string
  storyText: string
  title: string
  mode: 'auto' | 'human'
  status: 'idle' | 'queued' | 'running' | 'paused' | 'done' | 'error'
  currentAgent: string | null
  jobId: string | null
  queuePosition: number
  createdAt: number
}

interface StoryStore {
  stories: Story[]
  activeStoryId: string | null

  addStory: (story: Story) => void
  removeStory: (storyId: string) => void
  setActiveStory: (storyId: string) => void
  updateStory: (storyId: string, updates: Partial<Story>) => void
  getActiveStory: () => Story | undefined
}

export const useStoryStore = create<StoryStore>((set, get) => ({
  stories: [],
  activeStoryId: null,

  addStory: (story) =>
    set((state) => ({
      stories: [...state.stories, story],
      activeStoryId: story.storyId,
    })),

  removeStory: (storyId) =>
    set((state) => {
      const stories = state.stories.filter((s) => s.storyId !== storyId)
      const activeStoryId =
        state.activeStoryId === storyId
          ? (stories[0]?.storyId ?? null)
          : state.activeStoryId
      return { stories, activeStoryId }
    }),

  setActiveStory: (storyId) => set({ activeStoryId: storyId }),

  updateStory: (storyId, updates) =>
    set((state) => ({
      stories: state.stories.map((s) =>
        s.storyId === storyId ? { ...s, ...updates } : s,
      ),
    })),

  getActiveStory: () => {
    const { stories, activeStoryId } = get()
    return stories.find((s) => s.storyId === activeStoryId)
  },
}))
