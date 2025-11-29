/**
 * React Query hooks for job data.
 */

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { JobSummary, JobDetails } from '@/types';

interface UseJobsOptions {
  workflow_id?: string;
  robot_id?: string;
  status?: string;
  limit?: number;
  offset?: number;
}

export function useJobs(options: UseJobsOptions = {}) {
  const { workflow_id, robot_id, status, limit = 50, offset = 0 } = options;

  return useQuery<JobSummary[]>({
    queryKey: ['jobs', workflow_id, robot_id, status, limit, offset],
    queryFn: async () => {
      const { data } = await apiClient.get('/api/v1/metrics/jobs', {
        params: {
          workflow_id,
          robot_id,
          status,
          limit,
          offset,
        },
      });
      return data;
    },
    refetchInterval: 10000, // Refetch every 10 seconds
  });
}

export function useJobDetails(jobId: string) {
  return useQuery<JobDetails>({
    queryKey: ['job', jobId],
    queryFn: async () => {
      const { data} = await apiClient.get(`/api/v1/metrics/jobs/${jobId}`);
      return data;
    },
    enabled: !!jobId,
  });
}
