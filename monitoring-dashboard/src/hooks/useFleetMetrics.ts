/**
 * React Query hooks for fleet metrics.
 */

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { FleetMetrics } from '@/types';

export function useFleetMetrics() {
  return useQuery<FleetMetrics>({
    queryKey: ['fleet', 'metrics'],
    queryFn: async () => {
      const { data } = await apiClient.get('/api/v1/metrics/fleet');
      return data;
    },
    refetchInterval: 10000, // Refetch every 10 seconds
    staleTime: 5000, // Consider data stale after 5 seconds
  });
}
