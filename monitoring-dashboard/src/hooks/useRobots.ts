/**
 * React Query hooks for robot data.
 */

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { RobotSummary, RobotMetrics } from '@/types';

export function useRobots(status?: string) {
  return useQuery<RobotSummary[]>({
    queryKey: ['robots', status],
    queryFn: async () => {
      const { data } = await apiClient.get('/api/v1/metrics/robots', {
        params: { status },
      });
      return data;
    },
    refetchInterval: 15000, // Refetch every 15 seconds
  });
}

export function useRobotDetails(robotId: string) {
  return useQuery<RobotMetrics>({
    queryKey: ['robot', robotId],
    queryFn: async () => {
      const { data } = await apiClient.get(`/api/v1/metrics/robots/${robotId}`);
      return data;
    },
    enabled: !!robotId,
    refetchInterval: 10000, // Refetch every 10 seconds
  });
}
