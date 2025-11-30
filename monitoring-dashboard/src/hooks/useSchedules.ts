/**
 * React Query hooks for schedule data.
 *
 * Provides queries and mutations for the schedules API:
 * - useSchedules: Fetch all schedules
 * - useToggleSchedule: Enable/disable a schedule
 * - useTriggerSchedule: Manually trigger a schedule
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

export interface Schedule {
  schedule_id: string;
  workflow_id: string;
  schedule_name: string;
  cron_expression: string;
  enabled: boolean;
  priority: number;
  execution_mode: 'lan' | 'internet';
  next_run: string | null;
  last_run: string | null;
  run_count: number;
  failure_count: number;
  created_at: string;
}

interface SchedulesResponse {
  schedules: Schedule[];
  total: number;
}

interface UseSchedulesOptions {
  enabled?: boolean;
  workflow_id?: string;
  limit?: number;
  offset?: number;
}

interface ToggleSchedulePayload {
  schedule_id: string;
  enabled: boolean;
}

interface TriggerSchedulePayload {
  schedule_id: string;
  variables?: Record<string, unknown>;
}

interface TriggerScheduleResponse {
  job_id: string;
  schedule_id: string;
  workflow_id: string;
  status: string;
}

/**
 * Fetches all schedules from the API.
 * Refetches every 30 seconds to keep next_run times current.
 */
export function useSchedules(options: UseSchedulesOptions = {}) {
  const { enabled = true, workflow_id, limit = 100, offset = 0 } = options;

  return useQuery<Schedule[]>({
    queryKey: ['schedules', workflow_id, limit, offset],
    queryFn: async () => {
      const { data } = await apiClient.get<SchedulesResponse>('/api/v1/schedules', {
        params: {
          workflow_id,
          limit,
          offset,
        },
      });
      return data.schedules;
    },
    enabled,
    refetchInterval: 30000, // Refetch every 30 seconds for updated next_run times
    staleTime: 10000, // Consider data stale after 10 seconds
  });
}

/**
 * Mutation to toggle a schedule's enabled state.
 * Optimistically updates the cache for immediate UI feedback.
 */
export function useToggleSchedule() {
  const queryClient = useQueryClient();

  return useMutation<Schedule, Error, ToggleSchedulePayload, { previousSchedules: Schedule[] | undefined }>({
    mutationFn: async ({ schedule_id, enabled }) => {
      const { data } = await apiClient.patch<Schedule>(
        `/api/v1/schedules/${schedule_id}`,
        { enabled }
      );
      return data;
    },
    onMutate: async ({ schedule_id, enabled }) => {
      // Cancel outgoing refetches to avoid overwriting optimistic update
      await queryClient.cancelQueries({ queryKey: ['schedules'] });

      // Snapshot previous value
      const previousSchedules = queryClient.getQueryData<Schedule[]>(['schedules']);

      // Optimistically update the cache
      queryClient.setQueryData<Schedule[]>(['schedules'], (old) => {
        if (!old) return old;
        return old.map((schedule) =>
          schedule.schedule_id === schedule_id
            ? { ...schedule, enabled }
            : schedule
        );
      });

      return { previousSchedules };
    },
    onError: (_error, _variables, context) => {
      // Rollback on error
      if (context?.previousSchedules) {
        queryClient.setQueryData(['schedules'], context.previousSchedules);
      }
    },
    onSettled: () => {
      // Invalidate to refetch fresh data
      queryClient.invalidateQueries({ queryKey: ['schedules'] });
    },
  });
}

/**
 * Mutation to manually trigger a schedule.
 * Creates a new job for the schedule's workflow.
 */
export function useTriggerSchedule() {
  const queryClient = useQueryClient();

  return useMutation<TriggerScheduleResponse, Error, TriggerSchedulePayload>({
    mutationFn: async ({ schedule_id, variables = {} }) => {
      const { data } = await apiClient.post<TriggerScheduleResponse>(
        `/api/v1/schedules/${schedule_id}/trigger`,
        { variables }
      );
      return data;
    },
    onSuccess: () => {
      // Invalidate schedules to update run counts and last_run
      queryClient.invalidateQueries({ queryKey: ['schedules'] });
      // Also invalidate jobs since a new job was created
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });
}

/**
 * Get upcoming runs across all enabled schedules.
 * Sorts by next_run ascending and limits results.
 */
export function useUpcomingRuns(limit: number = 5) {
  const { data: schedules, ...rest } = useSchedules();

  const upcomingRuns = schedules
    ?.filter((s) => s.enabled && s.next_run)
    .sort((a, b) => {
      if (!a.next_run || !b.next_run) return 0;
      return new Date(a.next_run).getTime() - new Date(b.next_run).getTime();
    })
    .slice(0, limit) ?? [];

  return {
    ...rest,
    data: upcomingRuns,
    schedules,
  };
}
