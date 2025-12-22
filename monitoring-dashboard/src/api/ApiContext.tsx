import { createContext, useContext, ReactNode } from 'react'
import { robotsApi, jobsApi, schedulesApi, apiKeysApi, dlqApi, analyticsApi } from './client'

interface ApiContextValue {
  robots: typeof robotsApi
  jobs: typeof jobsApi
  schedules: typeof schedulesApi
  apiKeys: typeof apiKeysApi
  dlq: typeof dlqApi
  analytics: typeof analyticsApi
}

const ApiContext = createContext<ApiContextValue | null>(null)

export function ApiProvider({ children }: { children: ReactNode }) {
  const value: ApiContextValue = {
    robots: robotsApi,
    jobs: jobsApi,
    schedules: schedulesApi,
    apiKeys: apiKeysApi,
    dlq: dlqApi,
    analytics: analyticsApi,
  }

  return <ApiContext.Provider value={value}>{children}</ApiContext.Provider>
}

export function useApi(): ApiContextValue {
  const context = useContext(ApiContext)
  if (!context) {
    throw new Error('useApi must be used within an ApiProvider')
  }
  return context
}
