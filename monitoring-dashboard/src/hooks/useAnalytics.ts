/**
 * React Query hooks for analytics data.
 */

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { AnalyticsSummary } from '@/types';

export function useAnalytics() {
  return useQuery<AnalyticsSummary>({
    queryKey: ['analytics'],
    queryFn: async () => {
      const { data } = await apiClient.get('/api/v1/metrics/analytics');
      return data;
    },
    refetchInterval: 30000, // Refetch every 30 seconds
    staleTime: 15000, // Consider data stale after 15 seconds
  });
}
